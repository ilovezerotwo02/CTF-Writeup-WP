#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/*
int sys(char *cmd){
    system(cmd);
}
*/

int init_func(){
    setvbuf(stdin,0,2,0);
    setvbuf(stdout,0,2,0);
    setvbuf(stderr,0,2,0);
    return 0;
}

int dofunc(){
    char buf[0x100] ;
        puts("input:");
        read(0,buf,0x100);
        printf(buf);      
    return 0;
}

int main(){
	init_func();
    dofunc();
    return 0;
}
//gcc fmt_str_once_no_sys.c -no-pie -z norelro -o fmt_str_once_no_sys_x64_nopie
//gcc fmt_str_once_no_sys.c -z norelro -o fmt_str_once_no_sys_x64_pie