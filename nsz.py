#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This if is needed as multiprocessing shouldn't include nsz
# as it won't be able to optain __main__.__file__ and so crash inside Keys.py
if __name__ == '__main__':
	import nsz
	import multiprocessing
	multiprocessing.freeze_support()
	nsz.main()
