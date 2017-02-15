# coding=UTF-8
import urllib
import urllib2
import os
import shutil
import time
import threading

def get_papers(filename):
	global ut_list, count_num
	rows = [i.replace('\n','').split('\t') for i in open(filename,'r').readlines()[1:]]
	uts = ["'"+j[0]+"'" for j in rows]
	print len(uts)
	ut_list = []
	count_num = 0
	temp_list = []
	for i in range(0,len(uts)):
		temp_list.append(uts[i])
		if (i+1)%10==0 or i==(len(uts)-1):
			ut_list.append(temp_list)
			temp_list=[]

def findstr(s,str0,str1,start=0):
	res = ""
	p0 = s.find(str0,start) 
	p1 = -1
	if p0>-1:
		p0 +=len(str0)
		p1 = s.find(str1,p0)
		if p1>-1 :
			res = s[p0:p1]
	return res

def get_sid():
	url = 'http://apps.webofknowledge.com/'
	sid = ""
	while True:
		try:
			response = urllib2.urlopen(url,timeout=60.0)
			s = response.read()
			p1 = s.find('SID=') + len('SID=')
			p2 = s.find('&product')
			sid = s[p1:p2]
			break
		except Exception,ex:
			print "Access SID Unsuccessfully: ", ex, 'retry...'
	return sid

def mydecode(p):
    r = []
    for s in p.split('&'):
        s = urllib.unquote(s)  #.mydecode('utf8')
        p1 = s.find('=')
        r.append((s[0:p1],s[p1+1:]))
    return r

def openurl(url,sid, postdata, fname):
	headers = {}
	headers['cookie'] =  'SID='+sid+'; CUSTOMER="UNIV OF ELECTRONIC SCIENCES AND TECH OF CHINA - UESTC"; E_GROUP_NAME="University of Electronic Science and Technology of China"'
	headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'   
	
	status = 'GETTING'
	req = urllib2.Request(url, postdata, headers)
	while True: #直到成功访问链接，否则一直循环尝试
		try:
			response = urllib2.urlopen(req, timeout=60.0) #设置超时时间
			s=response.read()
			break
		except Exception,ex:
			print "FAINLING IN GETTING DATA FROM URL: ", ex, 'retry...'
			response = None
	if response is None: #异常后，设置的状态
		status = 'TIME-OUT'
	else:
		status = 'OK'
		file(fname,'w').write(s)
	return status

def paper_query(threadname):
	print 'start '+threadname
	while len(ut_list)>0:
		sid = get_sid()
		str_query = "ut=("+' or '.join(ut_list[0])+")"
		del ut_list[0]
		url_query = 'http://apps.webofknowledge.com/WOS_AdvancedSearch.do'
		datastr = 'product=WOS&search_mode=AdvancedSearch&action=search&goToPageLoc=SearchHistoryTableBanner&value(searchOp)=search'
		data = mydecode(datastr)
		data.append(('SID',sid))
		data.append(('value(input1)',str_query))
		postdata = urllib.urlencode(data)
		fname = './'+threadname+'/temp/advanced_query.html'
		query_status = openurl(url_query,sid,postdata, fname)
		if query_status=='OK':
			s = file(fname, 'r').read()
			hrefstr = findstr(s, 'class="historyResults">', '</a>')
			href = findstr(hrefstr, '<a href="' , '" title=')
			qid = findstr(href, '&qid=', '&')
			p0 = href.find('?product=WOS')
			url_list = 'http://apps.webofknowledge.com/summary.do' + href[p0:]
			fname = './'+threadname+'/temp/result_list.html'
			display_status = openurl(url_list, sid,None, fname)
			if display_status=='OK':
				record_analy(threadname,fname,qid,sid)
			print '------'+str(len(ut_list))+'------'

def record_analy(threadname,fname,qid,sid):
	s = file(fname, 'r').read()
	nfiles = int(findstr(s, 'FINAL_DISPLAY_RESULTS_COUNT =', ';</script>'))
	for i in range(1,nfiles+1):
		url_record = "http://apps.webofknowledge.com/full_record.do?product=WOS&search_mode=AdvancedSearch&qid="+qid+"&SID="+sid+"&page=1&doc="+str(i)
		fname = './'+threadname+'/temp/full_record.html'
		record_status = openurl(url_record,sid, None, fname)
		if record_status=='OK':
			try:
				ut,py,cur_cit = cit_analy(threadname,fname,qid,str(i),sid)
				open('./'+threadname+'/out/cur_cit.txt','a').write('\t'.join((ut,py,cur_cit))+'\n')
				print '---'+threadname+':'+str(i)+'---'
			except Exception,ex:
				print 'something wrong in ', threadname, ex

def cit_analy(threadname,fname,qid,parentDoc,sid):
	s = file(fname, 'r').read()
	pystr = findstr(s,'Published:</span>'+'\n'+'<value>','</value>')
	py = pystr.split(' ')[-1]
	ut = findstr(s,'class="hitHilite">','</span>')
	cur_cit = '0'
	if not s.find('&REFID=')==-1:
		refid = findstr(s,'&REFID=','&') 
		url_ref = 'http://apps.webofknowledge.com/CitingArticles.do?product=WOS&REFID='+refid+'&SID='+sid+'&search_mode=CitingArticles&parentProduct=WOS&parentQid='+qid+'&parentDoc='+parentDoc+'&excludeEventConfig=ExcludeIfFromFullRecPage'
		fname = './'+threadname+'/temp/ref_list.html'
		ref_status = openurl(url_ref, sid,None, fname)
		if ref_status=='OK':
			cur_cit = cur_cit_analy(threadname,fname,qid,parentDoc,py,sid)
	return ut,py,cur_cit

def cur_cit_analy(threadname,fname,qid,parentDoc,py,sid):
	s = file(fname, 'r').read()
	new_qid = findstr(s, '&qid=', '&')
	url_analy ='http://apps.webofknowledge.com/RAMore.do?product=WOS&search_mode=CitingArticles&SID='+sid+'&qid='+new_qid+'&ra_mode=more&ra_name=PublicationYear&colName=WOS&viewType=raMore'
	fname = './'+threadname+'/temp/analyze.html'
	analy_status = openurl(url_analy,sid, None, fname)
	if analy_status=='OK':
		s = file(fname, 'r').read()
		i = 1
		per_cit = []
		while True:
			year_cit = findstr(s,'<label for="IY_'+str(i)+'">','</label>')
			if len(year_cit)>0:
				per_cit.append(year_cit)
				i+=1
			if len(year_cit)==0:
				break
		cur_cit = extr_cit(per_cit,py)
		return cur_cit

def extr_cit(per_cit,py):
	num = '0'
	for cit in per_cit:
		if py in cit:
			l = cit.find('(')
			r = cit.find(')')
			num = cit[l+1:r]
			break
	return num

def my_thread(threads_num):
	threads = [] 
	for i in range(0,threads_num):
		threadname = 'thread'+str(i+1)
		if not os.path.exists('./'+threadname): 
			os.mkdir('./'+threadname)
		if not os.path.exists('./'+threadname+'/temp'):
			os.mkdir('./'+threadname+'/temp') 
		if not os.path.exists('./'+threadname+'/out'):
			os.mkdir('./'+threadname+'/out')  
		t = threading.Thread(target=paper_query,args=(threadname,))
		threads.append(t)
   	for i in range(0,len(threads)):
   		threads[i].start()
   		time.sleep(3) 
   	for thread in threads:
   		thread.join()

if __name__ == '__main__':
	get_papers('uestc_2015.txt')
	print 'start time:',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
	my_thread(5)
	print 'end time:',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))