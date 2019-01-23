import numpy as np
import math
import os
import random
from PIL import Image
import numpy as np
import osgeo
import rasterio
import numpy as np 
import time
import threading
from multiprocessing.dummy import Pool as ThreadPool 
from multiprocessing import Process

vp = [2047 ,785,1.65]#x,y,z 1.499976

#edgex=vp[0]+ rangex
#edgey=vp[1]+ rangey

#limits of image for x->ax<x<ex
ax=1500
ex=3000

#limits of image for y->ay<y<ey
ay=600
ey=1000


threadLock = threading.Lock()


#tif file with heights of every pixel
with rasterio.open('C:/Users/xrhstos/Desktop/DSM_Test.tif', 'r+') as r:

	d = r.read()  # read all raster values
data=d


def main():

	points_file="C:/Users/xrhstos/Desktop/Points_applied_to_DSM_and_Reference_from_row_1_to_2255.txt"
	
	#timer for scaning the image
	start_time = time.time()
	
	#height at the pixel of the observer
	vp[2]=d[0][vp[1]][vp[0]]+1.650000
	
	
	#grass output in order to compare with current output
	with rasterio.open('C:/Users/xrhstos/Desktop/Grass_x_cord_2048_and_y_cord_786.tif', 'r+') as a:
		d1 = a.read()  # read all raster values
		
		
	#function that calculates enter ,xit and center events for every pixel
	lst=rotation(d,vp)
	
	
	elapsed_time = time.time() - start_time
	print("elapsed_time for scanning the image",elapsed_time)

	#timer for visibility calculation
	start_time = time.time()
	
	#function that calculates visibility
	visibility(lst,d,d1,vp)
	
	elapsed_time = time.time() - start_time
	print("time passed for checking visibility",elapsed_time)
	
#binary search ->used to find pixels in the list
def bisearch(dist,target):

	current=len(dist)//2
	edge1=1
	edge2=len(dist)

	while dist[current-1]!=target :

		if dist[current-1]<target:

			if edge1!=current+1:
				edge1=current+1
				current+=(edge2-edge1)//2
			else:
				current+=1
		elif dist[current-1]>target:

			if edge2!=current-1:
				edge2=current-1
				current-=(edge2-edge1)//2
			else:
				current-=1


	while dist[current-2]==dist[current-1]:
		current-=1


	return current-1
	
#used binary search to find best possible spot for an elemnt that doesnt exist in the list	
def maxbisearch(dist,target):

	current=len(dist)//2
	edge1=0
	edge2=len(dist)-1

	while edge1<=edge2:

		current=(edge1+edge2)//2
		if dist[current]<=target:

			edge1=current+1
		elif dist[current]>target:

			edge2=current-1

	return edge1



#we are calculating height,angle and distance for every pixel and every type of event(center ,exit,enter)
def pixelevent(x,y,lst,x0,y0,x2,y2):

				#enter event height with interpolation
				x01=x
				x02=x+1*x0
				y01=y
				y02=y+1*y0
				q1=data[0][y01][x01]
				q2=data[0][y01][x02]
				q3=data[0][y02][x01]
				q4=data[0][y02][x02]
				height0=((q1+q2+q3+q4)/4)
				
				#exit event height with interpolation
				x01=x
				x02=x+1*x2
				y01=y
				y02=y+1*y2
				q1=data[0][y01][x01]
				q2=data[0][y01][x02]
				q3=data[0][y02][x01]
				q4=data[0][y02][x02]
				height2=((q1+q2+q3+q4)/4)
				
				#distance from observer for enter event
				distx=(x+(0.5*x0)-vp[0])*3
				disty=(y+(0.5*y0)-vp[1])*3
				distance0=math.sqrt(((disty)**2)+((distx**2)))	
				
				#distance from observer for enter event
				distx=(x-vp[0])*3
				disty=(y-vp[1])*3
				distance1=math.sqrt(((disty)**2)+((distx**2)))	
				
				#distance from observer for exit event
				distx=(x+(0.5*x2)-vp[0])*3
				disty=(y+(0.5*y2)-vp[1])*3
				distance2=math.sqrt(((disty)**2)+((distx**2)))
				
				#angle for enter event
				angle0=math.atan2((y+(0.5*y0)-vp[1]),(x+(0.5*x0)-vp[0]))
				#because atan2 returns nurmbers between π and -π when we find negative angles we add 2*π
				if angle0<0 :
					angle0+=2*math.pi
					
				#angle for center event					
				angle1=math.atan2((y-vp[1]),(x-vp[0]))
				#because atan2 returns nurmbers between π and -π when we find negative angles we add 2*π
				if angle1<0:
					angle1+=2*math.pi
				
				#angle for exit event
				angle2=math.atan2((y+(0.5*y2)-vp[1]),(x+(0.5*x2)-vp[0]))
				#because atan2 returns nurmbers between π and -π when we find negative angles we add 2*π
				if angle2<0:
					angle2+=2*math.pi
					
				
					
				#put the calculated values in the list
				lst.append([])
				lst[len(lst)-1].append(y)
				lst[len(lst)-1].append(x)
				lst[len(lst)-1].append(angle0)
				lst[len(lst)-1].append("ENTER")	
				lst[len(lst)-1].append(angle1)
				lst[len(lst)-1].append(angle2)
				lst[len(lst)-1].append(distance0)
				lst[len(lst)-1].append(distance1)
				lst[len(lst)-1].append(distance2)
				lst[len(lst)-1].append(height0)
				lst[len(lst)-1].append(height2)
				

				lst.append([])	
				lst[len(lst)-1].append(y)
				lst[len(lst)-1].append(x)
				lst[len(lst)-1].append(angle1)	
				lst[len(lst)-1].append("CENTER")

				lst.append([])
				lst[len(lst)-1].append(y)
				lst[len(lst)-1].append(x)
				lst[len(lst)-1].append(angle2)
				lst[len(lst)-1].append("EXIT")
				

		
def grid(y,lst):
		for x in range(ax,ex):
			#for events with angle=0
			if y==vp[1] and  x>vp[0] :

				pixelevent(x,y,lst,-1,-1,-1,+1)
			#for events with 0<angle<90			
			elif x>vp[0] and y>vp[1]:

				pixelevent(x,y,lst,+1,-1,-1,+1)
			#for events with angle=90	
			elif x==vp[0] and y>vp[1]:

				pixelevent(x,y,lst,+1,-1,-1,-1)
			#for events with 90<angle<180	
			elif x<vp[0] and y>vp[1]:

				pixelevent(x,y,lst,+1,+1,-1,-1)
			#for events with angle=180
			elif x<vp[0] and y==vp[1]:

				pixelevent(x,y,lst,+1,+1,+1,-1)		
			#for events with 180<angle<270	
			elif x<vp[0] and y<vp[1]:

				pixelevent(x,y,lst,-1,+1,+1,-1)
			#for events with angle=270	
			elif x==vp[0] and y<vp[1]:

				pixelevent(x,y,lst,-1,+1,+1,+1)				
			#for events with 270<angle<360	
			elif x>vp[0] and y<vp[1]:

				pixelevent(x,y,lst,-1,-1,+1,+1)		
				
			
class myThread (threading.Thread):
	def __init__(self,  y, lst):
		threading.Thread.__init__(self)

		self.y = y
		self.lst = lst
	def run(self):

		threadLock.acquire()
		grid(self.y,self.lst)

		threadLock.release()				
				
def rotation(data,vp):

	angle =0# 0

	counr=0
	lst = [] 
	
	y=ay
	
	while y<ey:	
		#for x in range(ax,ex):
		
			threads = []
			inc=8

			thread1 = myThread(y,lst)
			thread2 = myThread(y+1,lst)
			thread3 = myThread(y+2,lst)
			thread4 = myThread(y+3,lst)			
			thread5 = myThread(y+4,lst)
			thread6 = myThread(y+5,lst)			
			thread7 = myThread(y+6,lst)
			thread8 = myThread(y+7,lst)			
			

			thread1.start()
			thread2.start()
			thread3.start()
			thread4.start()
			thread5.start()
			thread6.start()	
			thread7.start()
			thread8.start()			
			
			
	# Add threads to thread list
			threads.append(thread1)
			threads.append(thread2)
			threads.append(thread3)
			threads.append(thread4)
			threads.append(thread5)
			threads.append(thread6)
			threads.append(thread7)
			threads.append(thread8)			
	# Wait for all threads to complete
			for t in threads:
				t.join()



	
			y+=inc

	return lst

def visibility(lst,data,datacomp,vp):
	check=0
	#max keeps the max height for every pixel at any point
	maxheight=[]
	#scalingmax keeps the max height we have until the pixel on the list
	scalingmax=[]
	totalmax=0

	lst=sorted(lst, key=lambda x: x[2])
	#currentx,y have the coordinates of every pixel currently on the list
	currentx=[]
	currenty=[]
	
	#currentdist have the distance from the observer for the enter-center and exit events
	currentdist0 = []
	currentdist1 = []
	currentdist2 = []
	
	#angle has the angle for the enter,center and exit event
	angle0 =[]
	angle1 =[]
	angle2 =[]
	
	#height has the height of enter and exit events
	height0= []
	height2 =[]
	
	#the variables bellow are used to messure the accuracy of the algorithm
	wronginv=0
	allpixel=0
	correctinv=0
	wrong=0
	correct=0


	img = Image.new( 'RGB', (3000,3000), "black")
	pixels = img.load()


	#the for bellow initialises the list with the values for angle=0
	for init in range(vp[0]+1,ex):
		
		#distance for center event for angle=0
		distx=(init-vp[0])*3
		disty=(0)*3
		distance=math.sqrt(((disty)**2)+((distx**2)))
		currentdist1.append(distance)
		distance1=distance
		
		#height for center event for angle=0 
		height1=data[0][vp[1]][init]
		m1=height1
		height=math.atan2((height1-vp[2]),(distance))

		#distance for enter event for angle=0
		distx=(init-0.5-vp[0])*3
		disty=(-0.5)*1
		distance=math.sqrt(((disty)**2)+((distx**2)))
		currentdist0.append(distance)
		distance0=distance
		
		#distance for exit event for angle=0
		distx=(init-0.5-vp[0])*3
		disty=(0.5)*1
		distance=math.sqrt(((disty)**2)+((distx**2)))
		currentdist2.append(distance)		
		distance2=distance
		
		#coordinates of the pixel
		currentx.append(init)
		currenty.append(vp[1])
		
		#angle for enter event for angle=0		
		angle=math.atan2((-0.5),(init-0.5-vp[0]))
		angle0.append(angle)

		#angle for center event for angle=0
		angle=math.atan2((0),(init-vp[0]))
		angle1.append(angle)

		#angle for exit event for angle=0		
		angle=math.atan2((+0.5),(init-0.5-vp[0]))
		angle2.append(angle)
		
		#calaculate height with interpollation for enter event
		x01=init
		x02=init-1
		y01=vp[1]
		y02=vp[1]-1
		q1=data[0][y01][x01]
		q2=data[0][y01][x02]
		q3=data[0][y02][x01]
		q4=data[0][y02][x02]
		height0.append((q1+q2+q3+q4)/4)
		m0=(q1+q2+q3+q4)/4
		
		#calaculate height through interpollation for exit event
		x01=init
		x02=init-1
		y01=vp[1]
		y02=vp[1]+1
		q1=data[0][y01][x01]
		q2=data[0][y01][x02]
		q3=data[0][y02][x01]
		q4=data[0][y02][x02]
		height2.append((q1+q2+q3+q4)/4)
		m2=(q1+q2+q3+q4)/4
		
		x1=init
		y2=vp[1]


		adj=distance1**2/(2*6370997)
		m1-=adj
		m1=math.atan2((m1-vp[2]),(distance1))
		

		adj=distance2**2/(2*6370997)
		m2-=adj
		m2=math.atan2((m2-vp[2]),(distance2))
	
		adj=distance0**2/(2*6370997)
		m0-=adj
		m0=math.atan2((m0-vp[2]),(distance0))
		
		curemax=max(m0,m2,m1)


		maxheight.append(curemax)	

	#---------------------------------------------------------START-------------------------------------------------------------
	#pull events one by one from the list
	for count1 in range(0,len(lst)):
		
		#distance to pixel for the event
		distx=(lst[count1][1]-vp[0])*3
		disty=(lst[count1][0]-vp[1])*3
		distance=math.sqrt(disty**2+distx**2)	
	
		
		x1=lst[count1][1]
		y2=lst[count1][0]

		#adjust height for curvature of the earth
		height=data[0][y2][x1]
		h1=height
		adj=distance**2/(2*6370997)
		height-=adj
		adjhei=height
		height=math.atan2((height-vp[2]),(distance))



		#in the enter event we input the new pixel in the list based on distance	
		if lst[count1][3]=="ENTER" :


			failsafe=len(currentdist1)
			#before binary search we check if the new event is the min or the max of the list 
			#and has to go first or last in the list
			
			#this i checks if its bigger than the max 
			if currentdist1[len(currentdist1)-1]<distance:
				i=len(currentdist1)

			#this  checks if its less than the min 	
			elif  currentdist1[0]>distance:
				i=0

			#here we do binary search to find the spot the pixels fits in based on distance
			else:
					
				i=maxbisearch(currentdist1,distance)

			currentx.insert(i,lst[count1][1])
			currenty.insert(i,lst[count1][0])

			angle0.insert(i,lst[count1][2])
			angle1.insert(i,lst[count1][4])
			angle2.insert(i,lst[count1][5])
			currentdist0.insert(i,lst[count1][6])
			currentdist1.insert(i,lst[count1][7])
			currentdist2.insert(i,lst[count1][8])
			height0.insert(i,lst[count1][9])	
			height2.insert(i,lst[count1][10])	


			m2=lst[count1][10]
			adj=lst[count1][8]**2/(2*6370997)
			m2-=adj
			m2=math.atan2((m2-vp[2]),(lst[count1][8]))
			
			m0=lst[count1][9]
			adj=lst[count1][6]**2/(2*6370997)
			m0-=adj
			m0=math.atan2((m0-vp[2]),(lst[count1][6]))
			
			curemax=max(m0,m2,height)

			maxheight.insert(i,curemax)


		#in exit events we delete from the list the pixel
		elif lst[count1][3]=="EXIT" :

			i=bisearch(currentdist1,distance)

			del currentdist0[i]
			del currentdist1[i]
			del currentdist2[i]
			del currentx[i]
			del currenty[i]
			del angle0[i]
			del angle1[i]
			del angle2[i]
			del height0[i]
			del height2[i]
			del maxheight[i]


		#	temp=max
		#	temp.sort()
		#	totalmax=temp[len(temp)-1]
			

		
		#in the center event we check for visibility
		elif lst[count1][3]=="CENTER":


	
			maxvis=-10000
			#we find the position of the event on the list
			countvis=bisearch(currentdist1,distance)


			#for the pixels with less distance than our current pixel we calculate their height
			#totalmax=max(maxheight)
		#	for i in range(0,countvis,1):
			#for i in range(0,countvis):
			#	print(maxheight[i])
			#	print(scalingmax[i])
			#	input()
						
					
			for i in range(0,countvis,1):
				
				#calculate height of current event with curvature of the earth
				height1=data[0][currenty[i]][currentx[i]]
				adj=currentdist1[i]**2/(2*6370997)
				height1-=adj
				
				height1=math.atan2((height1-vp[2]),(currentdist1[i]))
##################################################################################################################	
				
				#for the pixels with distance less than the current pixel we calculate their height
				#based on their enter ,center and exit angle and their enter exit and cnter height using interpolation
				#maxvis=maxheight[i]
				#maxvis=height-1
				#if adj>0.5:
				#	print("hue")
				#	input()
			
				#print(adj)
				#input()
				if  maxheight[i]>=height : #	if totalmax==maxheight[i] and maxheight[i]>h1:


				
					if(lst[count1][2]<angle1[i]):
					
							
							#adjust height for curve of the earth
							h0=height0[i]
							adj=currentdist0[i]**2/(2*6370997)
							h0-=adj
							h0=math.atan2((h0-vp[2]),(currentdist0[i]))

							#we calculate the height of the pixel in the list based on its enter ,center and exit angle and their
							#enter exit and cnter height using interpolation						
							curheight=height1+(h0-height1)*(angle1[i]-lst[count1][2])/(angle1[i]-angle0[i])

					elif(lst[count1][2]>angle1[i]):
					
							#adjust height for curve of the earth
							h2=height2[i]
							adj=currentdist2[i]**2/(2*6370997)
							h2-=adj
							h2=math.atan2((h2-vp[2]),(currentdist2[i]))
							#we calculate the height of the pixel in the list based on its enter ,center and exit angle and their
							#enter exit and cnter height using interpolation
							curheight=height1+(h2-height1)*(lst[count1][2]-angle1[i])/(angle2[i]-angle1[i])
					else:

	#############################################################################################							
						curheight=height1

					if maxvis<curheight:
						maxvis=curheight	
					if maxvis>height:
					
						break

			#	if curheight>height and maxheight[i]<h1:
			#		print("fmlip")
			#		input()
					
					

						
			#we print the pixels into an image
			if maxvis<height :

				if(datacomp[0][y2][x1]==1):
						#pixels[x1-vp[0]+rangex,y2-vp[1]+rangey] = (0, 100, 0)
					correct+=1
					pixels[x1-vp[0]+vp[0]-ax,y2-vp[1]+vp[1]-ay] = (0, 100, 0)
				else:
					#	pixels[x1-vp[0]+rangex,y2-vp[1]+rangey] = (255, 255, 0)
					wrong+=1
						#input()
		
				allpixel+=1
			else:
				
				if(datacomp[0][y2][x1]==1):
					wronginv+=1
					#	pixels[x1-vp[0]+rangex,y2-vp[1]+rangey] = (255, 255, 0)
				else:
					correctinv+=1
					pixels[x1-vp[0]+vp[0]-ax,y2-vp[1]+vp[1]-ay]  = (100, 0, 0) # set the colour accordingly
				allpixel+=1
				

	img.show()

	print("allpixel",allpixel)
	print("wrongpixel",wrong,"invisible pou einai visible",wronginv)
	print("correctpixel",correct,"invvisible pou einai inv",correctinv)
	#print(check)

main()