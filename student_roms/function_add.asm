section "header", rom0[$0100]
entrypoint:
    di
    jp main
    ds ($0150 - @), 0

main:
    ld hl, $FFFF
    ld bc, 10
    dec bc
    inc hl
    call add_nums
    swap a

add_nums:
    ret