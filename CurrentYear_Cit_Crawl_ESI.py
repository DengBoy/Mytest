#coding:utf-8
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from nt import chdir
import time
import os
import threading

def paper_info(filename):
	global papers,unlock_uts
	rows = [i.replace('\n','').split('\t') for i in open(filename,'r').readlines()[1:]]
	papers = [[j[0],j[1]] for j in rows]
	print 'paper number of filename is %s' %len(papers)
	unlock_uts = [i for i in range(len(papers))]

def click(browser,xpath,sleeptime=2):
	response = None
	try:
		wait = WebDriverWait(browser,120)
		wait.until(lambda x: x.find_element_by_xpath(xpath))	
		element = browser.find_element_by_xpath(xpath)
		browser.execute_script("arguments[0].scrollIntoView();", element) #拖动滚动条到元素可见的地方
		element.click()
		time.sleep(2)
		response = True
	except Exception,ex:
		response = False
	return response

def find_element(browser,xpath):
	response = None
	try:
		browser.find_element_by_xpath(xpath)
		response = True
	except Exception,ex:
		response = False
	return response

def extr_cit(cit_str,py):
	num = '0'
	per_cit = cit_str.encode('utf-8').strip().split('\n')
	for cit in per_cit:
		if py in cit:
			l = cit.find('(')
			r = cit.find(')')
			num = cit[l+1:r]
			break
	return num

def cit_current():
	drive_state = None
	for i in range(3):
		try:
			browser = webdriver.Chrome()
			host = 'http://apps.webofknowledge.com/' #打开主页而
			browser.get(host)
			xpath = "//a[@id='databases']" 
			if click(browser,xpath):
				xpath = "//i[@id='collectionDropdown']/ul/li[2]/a" #选择核心数据库
				if click(browser,xpath):
					xpath = "//div[@class='select2-container j-custom-select select-criteria2']/a"
					if click(browser,xpath):
						xpath = "//select[@class='j-custom-select select-criteria2 select2-offscreen']/option[17]" #选择按入藏号检索
						click(browser,xpath)
						drive_state = True
						break
		except Exception,ex:
			print '浏览器启动超时，retry....'
	if drive_state is None:
		print '浏览器启动失败，线程退出！'
		exit()
	flag = 1
	while len(unlock_uts)>0:
		try:
			paper_index = unlock_uts[0]
			ut = papers[paper_index][0]
			py = papers[paper_index][1]
			unlock_uts.remove(paper_index)
			num = None

			#获取文本框输入UT号
			if flag==1:#第一次检索
				txt_input = browser.find_element_by_xpath("//input[@class='search-criteria-input ui-autocomplete-input']")
				txt_input.send_keys(ut)
			if flag>1:#返回继续检索
				txt_input = browser.find_element_by_xpath("//div[@class='search-criteria-input-wr']/input[@class='search-criteria-input']")
				txt_input.clear()
				txt_input.send_keys(ut)
			#提交并检索
			xpath = "//span[@class='searchButton']/input"
			if click(browser,xpath):
				#获取引用文献列表
				xpath = "//div[@class='search-results-data-cite']/a"
				if find_element(browser,xpath):
					if click(browser,xpath):
						xpath = "//div[@class='block-text-content-scorecard']/p[@class='viewScorecard']/a[@class='scoreCardOn']"
						if click(browser,xpath):
							xpath = "//table[@class='All_Cit_Level3']/tbody/tr[1]/td[2]/span/a"
							if find_element(browser,xpath):
								if click(browser,xpath):	
									#打开出版年筛选条件
									xpath = "//div[@id='PublicationYear']/h4/a" 
									if click(browser,xpath):
										py_list = browser.find_element_by_xpath("//div[@id='PublicationYear']/div[@class='refine-content']/div[@class='refine-subitem-list']").text
										num = extr_cit(py_list,py)
										if num=='0':
											#查看出版年更多选项
											xpath = "//a[@class='link-style1'][@id='PublicationYear']" 
											if find_element(browser,xpath):
												if click(browser,xpath):
													py_list = browser.find_element_by_xpath("//tr[@id='PublicationYear_raMore_tr']").text
													num = extr_cit(py_list,py)
											else:
												num=='0'
							else:
								num = '0'
				else:
					num = '0'
			cit_str = '\t'.join([ut,py,num])
			f = file('cur_year_cit.txt','a').write(cit_str+'\n')
			print '---%s---' %str(paper_index+1)
			#返回检索界面继续检索
			xpath = "//div[@id='skip-to-navigation']/ul[@class='breadCrumbs']/li[@class='nonSearchPageChevron']/a" 
			click(browser,xpath)
			flag+=1

		except Exception,ex:
			print '记录：%s 引用分析失败！' %ut
			f = file('long.txt','a').write(ut+'\n')
			xpath = "//div[@id='skip-to-navigation']/ul[@class='breadCrumbs']/li[@class='nonSearchPageChevron']/a" 
			click(browser,xpath)
			flag+=1
	
	browser.quit()

def my_thread(threads_num):
	threads = [] 
	for i in range(0,threads_num):
		threads_name = 'thread_'+str(i+1)
		t = threading.Thread(target=cit_current)
		threads.append(t)
   	for i in range(0,len(threads)):
   		threads[i].start() 
   		print 'start thread '+str(i+1)
   		time.sleep(10)
   	for thread in threads:
   		thread.join()

if __name__=='__main__':
	filename = 'ESI_Papers.txt'	
	paper_info(filename)
	f = open('cur_year_cit.txt','a').write('UT\tPY\twos_Cit\n')
	start_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
	print 'start time',start_time
	my_thread(1)
	end_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
	print 'end time',end_time

