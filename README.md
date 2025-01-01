# Unthrottle

Have you ever been so ~~horny~~ interested in a file but you found that the only way to
get it is to download it from some ludicrous file sharing service which imposes unreasonable
download speed throttling? Well no more! Now you can route your download through as many
proxies as you want to __unthrottle__ the download speed.

## How does it work?
The idea is very simple - downloading the file through `n` proxies should make the download
go `n` times faster (of course, you can't download faster than your network bandwith allows you to).

Basically you can `spawn` a new "downloader" instance, navigate the download page a bit to get to the
download link and that's it. The more instances you `spawn` the faster it will go (and the more you will
feel dead inside from solving all the CAPTCHAs).

## How do I use it?
Currently it's not very easy to get it running, you will need:
- tor
- chromium
- uv

If you have all of those you can do `uv run unthrottle` and get it running.

## Notes
Currently you can't provide your own proxy list / use a VPN to route the download. (Will add that very soon)
The only way is to use Tor.

Currently only keep2share works. Will add more file hosting services soon (+ a "manual" option to download from unsupported
services).

Ass covering: This is only for educational purposes.
