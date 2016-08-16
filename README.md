# Memset hook for `letsencrypt.sh`

This a hook for [letsencrypt.sh](https://github.com/lukas2511/letsencrypt.sh) (a [Let's Encrypt](https://letsencrypt.org/) ACME client) that allows you to use [Memset](https://www.memset.com/) DNS records to respond to `dns-01` challenges. Requires Python and your Memset account API key being in the environment.

## Installation

```
$ git clone https://github.com/lukas2511/letsencrypt.sh
$ cd letsencrypt.sh
$ mkdir hooks
$ git clone https://github.com/tnwhitwell/letsencrypt-memset-hook hooks/memset
$ pip install -r hooks/memset/requirements.txt
```
If using Python 2, replace the last step with the one below and check the [urllib3 documentation](http://urllib3.readthedocs.org/en/latest/security.html#installing-urllib3-with-sni-support-and-certificates) for other possible caveats.

```
$ pip install -r hooks/cloudflare/requirements-python-2.txt
```


## Configuration

Your Memset account's [API key](https://www.memset.com/control/api/keys/) is expected to be in the environment, so make sure to:

```
$ export MEMSET_KEY='K9uX2HyUjeWg5AhAb'
```

### Key requirements:

The key should have access to at least:
 - job.status
 - dns.reload
 - dns.zone_domain_list
 - dns.zone_info
 - dns.zone_record_create
 - dns.zone_record_delete

Optionally, you can specify the DNS servers to be used for propagation checking via the `MEMSET_DNS_SERVERS` environment variable (props [bennettp123](https://github.com/bennettp123)):

```
$ export MEMSET_DNS_SERVERS='8.8.8.8 8.8.4.4'
```

Alternatively, these statements can be placed in `letsencrypt.sh/config.sh`, which is automatically sourced by `letsencrypt.sh` on startup:

```
echo "export MEMSET_KEY='K9uX2HyUjeWg5AhAb'" >> config.sh
```




## Usage

```
$ ./letsencrypt.sh -c -d example.com -t dns-01 -k 'hooks/memset/hook.py'
#
# !! WARNING !! No main config file found, using default config!
#
Processing example.com
 + Signing domains...
 + Creating new directory /home/user/letsencrypt.sh/certs/example.com ...
 + Generating private key...
 + Generating signing request...
 + Requesting challenge for example.com...
 + Memset hook executing: deploy_challenge
 + Waiting 10s for DNS reload to complete....
 + Reload not complete. Waiting another 10s....
 + Settling down for 10s...
 + DNS not propagated, waiting 30s...
 + DNS not propagated, waiting 30s...
 + Responding to challenge for example.com...
 + Memset hook executing: clean_challenge
 + Challenge is valid!
 + Requesting certificate...
 + Checking certificate...
 + Done!
 + Creating fullchain.pem...
 + Memset hook executing: deploy_cert
 + ssl_certificate: /home/user/letsencrypt.sh/certs/example.com/fullchain.pem
 + ssl_certificate_key: /home/user/letsencrypt.sh/certs/example.com/privkey.pem
 + Done!
```

## Credits
This is entirely thanks to [kappatamu/letsencrypt-cloudflare-hook](https://github.com/kappataumu/letsencrypt-cloudflare-hook) where I got the inspiration, and methodology. Updated to make it compatible with the Memset DNS manager.
