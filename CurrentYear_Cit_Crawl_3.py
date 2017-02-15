#coding:utf-8
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from nt import chdir
import time
import os
import threadpool

def paper_info(filename):
	rows = [i.replace('\n','').split('\t') for i in open(filename,'r').readlines()[1:]]
	papers = ['-'.join([j[60],j[44]]) for j in rows]
	print 'paper number of filename is %s' %len(papers)
	return papers

def click(browser,xpath,sleeptime=2):
	response = None
	try:
		wait = WebDriverWait(browser,30)
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

def cit_current(paper_info):
	ut = paper_info.split('-')[0]
	py = paper_info.split('-')[1]
	try:
		num = None
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
					if click(browser,xpath):
						txt_input = browser.find_element_by_xpath("//input[@class='search-criteria-input ui-autocomplete-input']")
						txt_input.send_keys(ut)
						xpath = "//span[@class='searchButton']/input"#提交并检索
						if click(browser,xpath):
							xpath = "//div[@class='search-results-data-cite']/a"
							if find_element(browser,xpath):
								if click(browser,xpath):
									xpath = "//div[@id='PublicationYear']/h4/a" #打开出版年筛选条件
									if click(browser,xpath):
										py_list = browser.find_element_by_xpath("//div[@id='PublicationYear']/div[@class='refine-content']/div[@class='refine-subitem-list']").text
										num = extr_cit(py_list,py)
										if num=='0':
											xpath = "//a[@class='link-style1'][@id='PublicationYear']" #查看出版年更多选项
											if find_element(browser,xpath):
												if click(browser,xpath):
													py_list = browser.find_element_by_xpath("//tr[@id='PublicationYear_raMore_tr']").text
													num = extr_cit(py_list,py)
											else:
												num=='0'
							else:
								num = '0'
		cit_str = '\t'.join([ut,py,num])
		f = file('cur_year_cit.txt','a').write(cit_str+'\n')
		print '---%s---' %ut
		browser.quit()

	except Exception,ex:
		print '记录：%s 引用分析失败！' %ut
		f = file('long.txt','a').write(ut+'\n')
		browser.quit()

if __name__=='__main__':
	filename = '1-University_of_Electronic_Science_&_Technology_of_China.txt'	
	papers = paper_info(filename)
	f = open('cur_year_cit.txt','a').write('UT\tPY\twos_Cit\n')
	pool = threadpool.ThreadPool(10)
	requests = threadpool.makeRequests(cit_current,papers)
	start_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
	print 'start time',start_time
	for req in requests:
		pool.putRequest(req)
		time.sleep(10)
	pool.wait()
	end_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
	print 'end time',end_time

