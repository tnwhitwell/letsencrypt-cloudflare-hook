#!/usr/bin/env python
from jsonrpclib import Server
from tld import get_tld
import dns.exception
import dns.resolver
import logging
import os
import sys
import time

memkey = os.environ['MEMSET_KEY']

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

try:
    memkey = os.environ['MEMSET_KEY']
except KeyError:
    logger.error(" + Unable to locate Memset credentials in environment!")
    sys.exit(1)

try:
    dns_servers = os.environ['DNS_SERVERS']
    dns_servers = dns_servers.split()
except KeyError:
    dns_servers = False

uri = "https://%s:@api.memset.com/v1/jsonrpc/" % memkey

s = Server(uri)


def _has_dns_propagated(name, token):
    txt_records = []
    try:
        if dns_servers:
            custom_resolver = dns.resolver.Resolver()
            custom_resolver.nameservers = dns_servers
            dns_response = custom_resolver.query(name, 'TXT')
        else:
            dns_response = dns.resolver.query(name, 'TXT')
        for rdata in dns_response:
            for txt_record in rdata.strings:
                txt_records.append(txt_record)
    except dns.exception.DNSException:
        return False

    for txt_record in txt_records:
        if txt_record == token:
            return True

    return False


# https://www.memset.com/apidocs/methods_dns.html#dns.zone_domain_list
def _get_zone_id(domain):
    tld = get_tld('http://' + domain)
    r = s.dns.zone_domain_list()
    for zone in r:
        if zone["domain"] == tld:
            return zone["zone_id"]


def _strip_domain(fqdn):
    tld = get_tld('http://' + fqdn)
    return fqdn.replace(".%s" % tld, "")


# https://www.memset.com/apidocs/methods_dns.html#dns.zone_info
def _get_txt_record_id(zone_id, name, token):
    r = s.dns.zone_info(id=zone_id)
    try:
        for record in r["records"]:
            if record["address"] == token:
                if record["record"] == name:
                    record_id = record["id"]
    except IndexError:
        logger.info(" + Unable to locate record named %s" % name)
        return

    try:
        return record_id
    except UnboundLocalError:
        return

    return


# https://www.memset.com/apidocs/methods_dns.html#dns.zone_record_create
def create_txt_record(args):
    domain, token = args[0], args[2]
    zone_id = _get_zone_id(domain)

    fqdn = "%s.%s" % ('_acme-challenge', domain)
    name = _strip_domain(fqdn)

    r = s.dns.zone_record_create(zone_id=zone_id, type="TXT", record=name, address=token)
    record_id = r['id']
    logger.debug(" ++ TXT record created, ID: %s" % record_id)

    r = s.dns.reload()
    reload_id = r['id']
    logger.info(" + Waiting 10s for DNS reload to complete....")
    time.sleep(10)
    while not s.job.status(id=reload_id)["finished"]:
        logger.info(" + Reload not complete. Waiting another 10s....")
        time.sleep(10)

    # give it 10 seconds to settle down and avoid nxdomain caching
    logger.info(" + Settling down for 10s...")
    time.sleep(10)

    while not _has_dns_propagated(fqdn, token):
        logger.info(" + DNS not propagated, waiting 30s...")
        time.sleep(30)


# https://www.memset.com/apidocs/methods_dns.html#dns.zone_record_delete
def delete_txt_record(args):
    domain, token = args[0], args[2]
    if not domain:
        logger.info(" + http_request() error in letsencrypt.sh?")
        return

    zone_id = _get_zone_id(domain)

    fqdn = "%s.%s" % ('_acme-challenge', domain)
    name = _strip_domain(fqdn)

    record_id = _get_txt_record_id(zone_id, name, token)

    logger.debug(" ++ Deleting TXT record name: %s" % name)

    s.dns.zone_record_delete(id=record_id)


def deploy_cert(args):
    domain, privkey_pem, cert_pem, fullchain_pem, chain_pem, timestamp = args
    logger.info(' + ssl_certificate: %s' % fullchain_pem)
    logger.info(' + ssl_certificate_key: %s' % privkey_pem)
    return


def unchanged_cert(args):
    return


def main(argv):
    ops = {
        'deploy_challenge': create_txt_record,
        'clean_challenge': delete_txt_record,
        'deploy_cert': deploy_cert,
        'unchanged_cert': unchanged_cert,
    }
    logger.info(" + Memset hook executing: %s" % argv[0])

    ops[argv[0]](argv[1:])


if __name__ == '__main__':
    main(sys.argv[1:])
