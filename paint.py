#!/usr/bin/python
__author__ = 'mwvaughn'

import argparse
import subprocess
import sys
import os
import errno
import time
from random import randint
from multiprocessing import Queue, Process

extra_arguments = "-cudnn_autotune -backend cudnn -image_size 512"

def render_worker( work_queue, done_queue ):

    for cmd in iter( work_queue.get, 'STOP' ):
        print 'Rendering ' + cmd
        #os.system( cmd )
        print 'Rendered'
        done_queue.put('Success: ' + cmd)

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

    render_queue = []
    for z in range( gpus ):
        q = Queue()
        render_queue.append(q)

    done_queue = Queue()
    processes = []

# Figure out frame count
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

# Submit tasks
    for i in xrange(frame_i, nrframes, gpus):
        for g in range(gpus):
            frame_j = i + g
            #print 'frame_j ' + str(frame_j)

            if frame_j <= nrframes:
                print 'Frame: {}'.format(frame_j)
                print 'GPU: ' + str(g)
                command = "th neural_style.lua " + extra_arguments + " -gpu " + str(g) + " -num_iterations 1000 -style_image " + style + " -content_image " + input + "/%08d.jpg" % frame_j + " -save_iter 2000 -output_image " + output + "/%08d.jpg" % frame_j
                render_queue[g].put(command)

# Start worker processes
    for w in xrange( gpus ):
        Process(target=render_worker, args=(render_queue[w], done_queue)).start()

# Print output queue
    for i in xrange(nrframes):
        print done_queue.get()

# Send STOP
    for zz in xrange( gpus ):
        render_queue[zz].put('STOP')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Implementing neural art on video.')
    parser.add_argument(
        '-g','--gpus',
        help='Number of host GPUs', type=int, default=4,
        required=False)
    parser.add_argument(
        '-x','--extra_arguments',
        help='Other arguments', default='-cudnn_autotune -backend cudnn -image_size 512',
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

    main(args.input, args.output, args.style, args.start_frame, args.end_frame, args.gpus, args.extra_arguments)
