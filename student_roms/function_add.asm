section "header", rom0[$0100]
entrypoint:
    di
    jp main
    ds ($0150 - @), 0

main:
    ld d, 100
    ld a, d
    call add_nums
    xor a

add_nums:
    add a, d
    ret