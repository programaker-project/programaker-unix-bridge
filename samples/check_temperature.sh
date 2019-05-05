#!/bin/sh

while [ 1 ];do
	acpi -t|awk '{print $4;}' | tee ~/.config/plaza/bridges/unix/pipes/on_new_temparature
	sleep 10
done
