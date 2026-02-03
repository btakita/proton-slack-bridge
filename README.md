# proton-slack-bridge
Service to connect Proton Main Bridge with Slack. Python prototype. May migrate to golang or zig.

# Future Plans

## Why Zig?

Zig would allow this library to be embeddable in other programming languages.

Using [lazily-zig](https://github.com/btakita/lazily-zig) + FFI, the host runtime can
use an api to get/set state.
This would remove the need to have a separate service on a host runtime.

## Why Golang?

Golang has a mature ecosystem for IMAP and running services in general.

Would be faster to develop as a standalone service.

## Which way am I leaning right now?

I'm favoring Zig due to making this an embeddable library with an optional standalone service.

This would also allow me to convert the Python prototype into a Python front-end package.
