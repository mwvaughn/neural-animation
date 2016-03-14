#!/usr/bin/python
__author__ = 'mwvaughn'

import argparse
import subprocess
import sys
import os
import errno
import time

import Queue
from threading import Thread

gpus = 4
extra_arguments = "-cudnn_autotune -backend cudnn -image_size 512"
# How many GPUs on system by default
render_queue = []
for z in range[ (gpus - 1) ]:
    q = Queue()
    render_queue.append[q]

def render(i, q):
    """This is the worker thread function.
    It processes items in the queue one after
    another.  These daemon threads go into an
    infinite loop, and only exit when
    the main thread ends.
    """
    while True:
        print '%s: Looking for the next render job' % i
        command = q.get()
        print 'Rendering ' + command
        # instead of really rendering
        # we just pretend and sleep
        time.sleep(i + 2)
        #os.system( command )
        q.task_done()

# Set up some threads to render frames
for i in range( (gpus - 1) ):
    worker = Thread(target=render, args=(i, render_queue[i],))
    worker.setDaemon(True)
    worker.start()

def make_sure_path_exists(path):
    '''
    make sure input and output directory exist, if not create them.
    If another error (permission denied) throw an error.
    '''
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def main(input, output, style, start_frame, end_frame, gpus, extra_arguments):
    make_sure_path_exists(input)
    make_sure_path_exists(output)

    nrframes =len([name for name in os.listdir(input) if os.path.isfile(os.path.join(input, name))])
    if nrframes == 0:
        print("Found no frames to process...")
        sys.exit(0)

    if start_frame is None:
     	frame_i = 1
    else:
	frame_i = int(start_frame)
    if not end_frame is None:
    	nrframes = int(end_frame)+1
    else:
	nrframes = nrframes+1

    # Cycle through GPUs, adding to queue
    # Risks leaving GPUs underutilized towards end of job list
    for i in xrange(frame_i, nrframes, num_gpus):
        for g in range(0, num_gpus - 1):
            frame_j = frame_i + g
            if frame_j <= nrframes:
                print 'Queueing on GPU ' + g
                print 'Frame #{}'.format(frame_j)
                command = "th neural_style.lua " + extra_arguments + "-gpu " + g + " -num_iterations 1000 -style_image " + style + " -content_image " + input + "/%08d.jpg" % frame_j + " -save_iter 2000 -output_image " + output + "/%08d.jpg" % frame_j
                render_queue[g].put(command)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Implementing neural art on video.')
    parser.add_argument(
        '-g','--gpus',
        help='Number of host GPUs', type=int, default=1,
        required=False)
    parser.add_argument(
        '-x','--extra_arguments',
        help='Other arguments', default='',
        required=False)
    parser.add_argument(
        '-i','--input',
        help='Input directory where extracted frames are stored',
        required=True)
    parser.add_argument(
        '-o','--output',
        help='Output directory where processed frames are to be stored',
        required=True)
    parser.add_argument(
	'-s','--style',
	help='Image to base the style after',
	required=True)
    parser.add_argument(
    	'-sf', '--start_frame',
        type=int,
    	required=False,
    	help="starting frame nr")
    parser.add_argument(
    	'-ef', '--end_frame',
        type=int,
    	required=False,
    	help="end frame nr")

    args = parser.parse_args()

    main(args.input, args.output, args.style, args.start_frame, args.end_frame, args.gpu, args.extra_arguments)
