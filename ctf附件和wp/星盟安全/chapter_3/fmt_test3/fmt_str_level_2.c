#include <stdio.h>
#include <unistd.h>
#include <string.h>
//HITCON-Training lab9
char buf[200] ;

/* int init_func(){ */
/*     setvbuf(stdin,0,2,0); */
/*     setvbuf(stdout,0,2,0); */
/*     setvbuf(stderr,0,2,0); */
/*     return 0; */
/* } */

void do_fmt(){
	while(1){
		read(0,buf,200);
		if(!strncmp(buf,"quit",4))
			break;
		printf(buf);
	}
	return ;
}

void play(){
	puts("hello");
	do_fmt();
	return;
}

int main(){
	/* init_func(); */
	play();
	return 0;
}
//gcc fmt_str_level_2.c -z lazy -o fmt_str_level_2_x64
//gcc -m32 fmt_str_level_2.c -z lazy -o fmt_str_level_2_x86
