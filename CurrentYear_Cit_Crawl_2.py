#coding:utf-8
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from nt import chdir
from multiprocessing import Process,Array
from ctypes import c_char_p
import time
import os
import threading 


#运行程序前先启动selenium-server-standalone.jar程序，在机器存放selenium-server-standalone.jar的路径下运行命令：java -jar selenium-server-standalone.jar -port 4446
def paper_info(filename):
	global papers,unlock_uts
	rows = [i.replace('\n','').split('\t') for i in open('2012_papers.txt','r').readlines()[1:]]
	papers = [[j[60],j[44]] for j in rows]
	print 'paper number of filename is %s' %len(papers)
	unlock_uts = [i for i in range(len(papers))]

def click(browser,xpath,sleeptime=2):
	response = False
	Wait_Time = 0
	while Wait_Time<=30:
		try:
			element = browser.find_element_by_xpath(xpath)
			browser.execute_script("arguments[0].scrollIntoView();", element) #拖动滚动条到元素可见的地方
			element.click()
			response = True
			time.sleep(2)
			break
		except Exception,ex:
			time.sleep(2)
			Wait_Time+=2
			print '链接%s获取失败,等待2s后重新解析....' %xpath
	if Wait_Time>30:
		print '等待超时,重新执行此记录....'
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
	#browser = webdriver.Chrome()
	browser = webdriver.Remote("http://localhost:4446/wd/hub", desired_capabilities=webdriver.DesiredCapabilities.HTMLUNIT)
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
					flag = 1
					while len(unlock_uts)>0:
						status = False
						paper_index = unlock_uts[0]
						ut = papers[paper_index][0]
						py = papers[paper_index][1]
						unlock_uts.remove(paper_index)
						num = '0'
						for i in range(5):
						#打开基础检索界面以入藏号进行检索，第一次检索和返回继续检索界面存在一些不同，需要判断。
							if flag==1:#第一次检索
								txt_input = browser.find_element_by_xpath("//input[@class='search-criteria-input ui-autocomplete-input']")
								txt_input.send_keys(ut)
							if flag>1:#返回继续检索
								'''xpath = "//i[@id='clearIcon1']"
								if click(browser,xpath):
									txt_input = browser.find_element_by_xpath("//div[@class='search-criteria-input-wr']/input[@class='search-criteria-input']")
									txt_input.send_keys(ut)'''
								txt_input = browser.find_element_by_xpath("//div[@class='search-criteria-input-wr']/input[@class='search-criteria-input']")
								txt_input.clear()
								txt_input.send_keys(ut)

							xpath = "//span[@class='searchButton']/input"#提交并检索
							if click(browser,xpath):
								flag+=1
								xpath = "//div[@class='search-results-data-cite']/a" #打开施引文献列表
								cit_num = browser.find_element_by_xpath(xpath).text.encode('utf8')
								if not cit_num =='0':
									if click(browser,xpath):
										if cit_type=='esi': #获取ESI被引频次
											xpath = "//div[@class='block-text-content-scorecard']/p[@class='viewScorecard']/a[@class='scoreCardOn']"
											click(browser,xpath)
											xpath = "//table[@class='All_Cit_Level3']/tbody/tr[1]/td[2]/span/a"
											if click(browser,xpath):
												response,num = analy_citpage(browser,py)
										
										if cit_type=='wos':#获取WOS被引频次
											xpath = "//div[@id='PublicationYear']/h4/a" #打开出版年筛选条件
											if click(browser,xpath):
												py_list = browser.find_element_by_xpath("//div[@id='PublicationYear']/div[@class='refine-content']/div[@class='refine-subitem-list']").text
												num = extr_cit(py_list,py)
												if num=='0':
													xpath = "//a[@class='link-style1'][@id='PublicationYear']" #查看出版年更多选项
													try:
														browser.find_element_by_xpath(xpath)
														if click(browser,xpath):
															py_list = browser.find_element_by_xpath("//tr[@id='PublicationYear_raMore_tr']").text
															num = extr_cit(py_list,py)
														else:
															print '第%s次重新执行此记录：%s' %(str(i+1),org_name)
															xpath = "//div[@id='skip-to-navigation']/ul[@class='breadCrumbs']/li[@class='nonSearchPageChevron']/a" #返回检索界面
															click(browser,xpath)
															continue
													except	Exception,ex:
														num=='0'
											else:
												print '第%s次重新执行此记录：%s' %(str(i+1),org_name)
												xpath = "//div[@id='skip-to-navigation']/ul[@class='breadCrumbs']/li[@class='nonSearchPageChevron']/a" #返回检索界面
												click(browser,xpath)
												continue
									else:
										print '第%s次重新执行此记录：%s' %(str(i+1),org_name)
										xpath = "//div[@id='skip-to-navigation']/ul[@class='breadCrumbs']/li[@class='nonSearchPageChevron']/a" #返回检索界面
										click(browser,xpath)
										continue
									cit_str = '\t'.join([ut,py,num])
									f = open('cur_year_cit.txt','a')
									f.write(cit_str+'\n')
									f.close()
									print '---'+str(paper_index+1)+'---'
									status = True
									xpath = "//div[@id='skip-to-navigation']/ul[@class='breadCrumbs']/li[@class='nonSearchPageChevron']/a" #返回检索界面
									click(browser,xpath)
									break
							else:
								print '第%s次重新执行此记录：%s' %(str(i+1),org_name)
								xpath = "//div[@id='skip-to-navigation']/ul[@class='breadCrumbs']/li[@class='nonSearchPageChevron']/a" #返回检索界面
								click(browser,xpath)
								continue

						if not status:
							print '记录：%s 引用分析失败！' %ut
							unlock_uts.append(paper_index)
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
	global cit_type,filename
	filename = '2012_papers.txt'
	cit_type = 'wos'	
	paper_info(filename)
	f = open('cur_year_cit.txt','a')
	f.write('UT\tPY\t'+cit_type+'_Cit\n')
	f.close()
	my_thread(3)