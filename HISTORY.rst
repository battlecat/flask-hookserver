.. :changelog:

History
-------

0.3.1 (2015-11-19)
++++++++++++++++++

- Accept unicode keys
- Default to true for VALIDATE_IP and VALIDATE_SIGNATURE if missing

0.3.0 (2015-11-08)
++++++++++++++++++

- Move hooks URL route into a blueprint
- Report rate limit expire time when the GitHub request limit is exceeded

0.2.1 (2015-10-21)
++++++++++++++++++

- Install Requests security dependencies

0.2.0 (2015-10-21)
++++++++++++++++++

- Proper Python 2.7 support
- Respect GitHub rate limit of 60 requests per hour
- Make key param to HookServer optional
- Add optional param url
- Use VALIDATE_IP and VALIDATE_SIGNATURE instead of DEBUG
- Simplify some error messages
- Add test suite

0.1.4 (2015-04-07)
++++++++++++++++++

- Support IPv4 addresses mapped to IPv6

0.1.3 (2014-07-10)
++++++++++++++++++

- Fix Python 2 bug in IP address decoding

0.1.2 (2014-07-09)
++++++++++++++++++

- Ignore HMAC in debug mode

0.1.1 (2014-07-08)
++++++++++++++++++

- Reload GitHub IP block on each request

0.1.0 (2014-07-07)
++++++++++++++++++

- Initial release
