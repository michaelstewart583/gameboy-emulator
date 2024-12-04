section "header", rom0[$0100]
entrypoint:
    di
    jp main
    ds ($0150 - @), 0

main:
    ld d, 100
loop:
    inc d
    jp nc, loop
ld d, d