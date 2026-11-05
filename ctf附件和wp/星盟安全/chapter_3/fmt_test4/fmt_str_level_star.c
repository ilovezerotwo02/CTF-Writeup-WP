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
    char buf1[8]={} ;
	char buf2[0x10];
	char buf3[8]={};
	long long int *p = (long long int)buf1 ;
	int fd = open("/dev/random",0);
	int d = 0	;	
	read(fd , buf1,2);
	read(fd , buf3,2);
	close(fd);
    puts("input:");
    read(0,buf2,0x10);
	printf(buf2);
	if(!strncmp(buf1,buf3,2))
	{
		system("/bin/sh");
	}
    return 0;
}

int main(){
	init_func();
    dofunc();
    return 0;
}
//gcc fmt_str_level_star.c  -o fmt_str_level_star_x64
//gcc -m32 fmt_str_level_star.c   -o fmt_str_level_star_x86
