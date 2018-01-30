
mov 1, r0
mov 1, r1
out r0
out r1

label jumppoint_fib
    add r0,r1,r0
    jc end
    out r0
    add r0,r1,r1
    jc end
    out r1
    jmp jumppoint_fib

    
label end
stp