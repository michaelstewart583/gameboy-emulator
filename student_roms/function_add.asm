section "header", rom0[$0100]
entrypoint:
    di
    jp main
    ds ($0150 - @), 0

main:
    ld a, 5
    .loop_one
        dec a
        cp a, 0
        jp nz, .loop_one
    
    ld a, 5
    .loop_two
        dec a
        cp a, 1
        jp nc, .loop_two

    ld a, 5
    sub a, 5
    jp z, .done

    ld a, 10

    .done
    ld a, 3
    sub a, 4
    jp c, .really_done

    ld a, 10

    .really_done
    ld a, 20




