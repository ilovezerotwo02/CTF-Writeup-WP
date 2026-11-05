#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int init_func(){
    setvbuf(stdin,0,2,0);
    setvbuf(stdout,0,2,0);
    setvbuf(stderr,0,2,0);
    return 0;
}

int dofunc(){
    char buf[0x100] ;
    while(1){
        puts("input:");
        read(0,buf,0x100);
		if(!strncmp(buf,"quit",4))
			break;
        printf(buf);      
    }
    return 0;
}

int main(){
    init_func();
    dofunc();
    return 0;
}
//gcc fmt_str_level_1.c -z lazy -o fmt_str_level_1_x64
//gcc -m32 fmt_str_level_1.c -z lazy -o fmt_str_level_1_x86
