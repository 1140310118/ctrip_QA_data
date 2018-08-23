from bs4 import BeautifulSoup
import requests
import random
import os
import threading
import time


my_headers=["Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0",
			"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
			'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0',
			'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36',
			'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36',
			'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER) ',  
			'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)']



def download_html(url,args={}):
	"""
	根据url及参数下载网页
	"""
	random_header = random.choice(my_headers)
	headers = {'User-Agent' : random_header}
	data = requests.get(url, headers=headers, params=args)
	data.encoding = 'utf-8'
	return data.text

def makedir(dir_):
	if not os.path.isdir(dir_):
		os.makedirs(dir_)



class Question:
	"""
	根据问题URL，爬取问题，然后写入指定文件中
	"""
	def __init__(self,url):
		self.url = url
		self.title = None
		self.content = None
		self.tags = []
		self.answers = []

	def get(self):
		html = download_html(self.url)
		if len(html)<1000:
			self.get()
			return 
		soup = BeautifulSoup(html,'html.parser')

		self.title = soup.find('h1',class_='ask_title').text.replace('\n','').strip()
		self.content = soup.find('p',class_='ask_text').text
		self.tags = [node.text for node in soup.find_all('a',class_='asktag_item')]
		self.answers = [node.text for node in soup.find_all('p',class_="answer_text")]
		
	def output_error(self,lst):
		with open('error.txt','w',encoding='utf-8') as file_out:
			for l in lst:
				file_out.write(l+'\n')


	def write(self,dir_):
		if not self.answers: # 回答为零的问题 不予保存
			return
		with open(dir_, 'w', encoding='utf-8') as file_out:
			file_out.write('[地址] %s\n\n'%self.url)
			file_out.write('[标题] %s\n\n'%self.title)
			file_out.write('[内容] %s\n\n'%self.content)
			file_out.write('[标签] %s\n\n'%', '.join(self.tags))
			for i,answer in enumerate(self.answers):
				text = "[回答 %d] %s\n\n"%(i,answer)
				file_out.write(text)


class Tag:
	"""
	根据标签URL，爬取问题链接
	# 举例

	tag_url='http://you.ctrip.com/asks/osaka293.html'
	t = Tag(tag_url)
	t.get_and_write("data/大阪/URL.txt")
	"""
	def __init__(self,url):
		self.url = url

	def get_and_write(self,dir_):
		with open(dir_, 'w', encoding='utf-8') as file_out:
			q_urls_part = -1
			while q_urls_part == -1:
				q_urls_part,html = self._get_q_urls_single(self.url)
			soup = BeautifulSoup(html,'html.parser')
			page = soup.find('div',class_='pager_v1')
			if not page: # 只有一页
				return 
			page = int(page.find_all('a')[-2].text) # 总页数
			for i in range(2,page+1):
				tag_url = self.url[:-5] + '-k3/p%d'%i + '.html'
				q_urls_part = -1
				while q_urls_part == -1:
					q_urls_part = self._get_q_urls_single(tag_url)[0]
				file_out.write('\n'.join(q_urls_part)+'\n')

	def read(self,dir_):
		q_urls = []
		with open(dir_, 'r', encoding='utf-8') as file_in:
			for line in file_in:
				if line:
					q_urls.append(line[:-1]) # 去掉换行符
		return q_urls

	def _get_q_urls_single(self,tag_url):
		"""
		单个标签页面
		"""
		html = download_html(tag_url)
		soup = BeautifulSoup(html,'html.parser')
		node  = soup.find('ul',class_="asklist")
		if node == None: 
			return -1,-1

		nodes = node.find_all('li',class_="cf")
		q_urls = []
		for node in nodes:
			url_ = 'http://you.ctrip.com'+(node['href'])
			q_urls.append(url_)
			
		return q_urls,html

class ZT:
	"""
	根据 问答专题URL 获得 标签URL
	# 举例

	zt_url='http://you.ctrip.com/asks/topics.html'
	zt = ZT(zt_url)
	zt.get_tags()
	zt.write('data/tag.txt')
	"""
	def __init__(self,url):
		self.url = url

	def _get_tags_single(self,zt_url):
		html = download_html(zt_url)
		soup = BeautifulSoup(html,'html.parser')
		nodes = soup.find_all('a',class_='asktag_item')
		if nodes == []:
			return -1
		tags_single = []
		for node in nodes:
			tags_single.append((node['href'],node['title']))
		return tags_single

	def get_tags(self):
		self.tags = set()
		for i in range(1,15):
			zt_url = self.url[:-5] + '-p%d.html'%i
			tags_single = -1
			while tags_single == -1:
				tags_single = self._get_tags_single(zt_url)
			self.tags = self.tags | set(tags_single) # 并
		return self.tags

	def write(self,dir_):
		f = lambda s:",".join(s)
		with open(dir_, 'w', encoding='utf-8') as file_out:
			file_out.write("\n".join([f(tag) for tag in self.tags]))

	def read(self,dir_):
		tags = []
		with open(dir_, 'r', encoding='utf-8') as file_in:
			for line in file_in:
				tag = line[:-1].split(',') # :-1 是为了去除换行符
				tags.append(tag)
		return tags



class Tag2qurls_Thread(threading.Thread):
	"""
	根据标签获取问题地址
	"""
	def __init__(self,tag_name,tag_url,count=1):
		threading.Thread.__init__(self)
		self.tag_name = tag_name
		self.tag_url = tag_url
		self.count = count

	def run(self):
		self.count += 1
		if self.count > 3: # 超过错误次数，退出
			print ("$",end=' ')
			return 
		try:
			full_url = 'http://you.ctrip.com' + self.tag_url
			makedir('data/%s'%self.tag_name)
			t = Tag(full_url)
			t.get_and_write('data/%s/URL.txt'%self.tag_name)
		except requests.exceptions.ConnectionError: # 连接超时
			time.sleep(2)
			print ("**",end=" ")
			Tag2qurls_Thread(self.tag_name,self.tag_url,self.count+1).start()


class Get_Question_Thread(threading.Thread):
	def __init__(self,url,dir_,count=1):
		self.url  = url
		self.dir_ = dir_
		self.count = count
		threading.Thread.__init__(self)
	def run(self):
		self.count += 1
		if self.count >3:
			print ("$",end=" ")
			return
		try:
			q = Question(self.url)
			q.get()
			q.write(self.dir_)
		except (requests.exceptions.ConnectionError, AttributeError): # 连接超时
			time.sleep(2)
			print ("**",end=" ")
			Get_Question_Thread(self.url,self.dir_,self.count+1).start()


def get_tags(zt_url,done=0):
	zt = ZT(zt_url)
	if not done:
		zt.get_tags() 
		zt.write('data/tag.txt')
	return zt.read('data/tag.txt') 

def get_q_urls(tags,done=0,thread_num=20):
	if done:
		return
	print ("共有%d个标签"%len(tags))
	for i,(url,name) in enumerate(tags): 
		print (i,name)
		while threading.activeCount()>thread_num:
			time.sleep(2)
			print ("..", end=" ")
		Tag2qurls_Thread(name,url).start()

def get_question(tags,thread_num=40):
	progress = lambda rate: "#"*int(rate*20)+" "*int(20-rate*20)
	for i,(url,name) in enumerate(tags):
		tag = Tag(url)
		q_urls = tag.read('data/%s/URL.txt'%name)
		urls_num = len(q_urls) 
		print ('\n ',i+1,name,"共%d个问题"%len(q_urls))
		for j,q_url in enumerate(q_urls):
			rate = (j+1)/urls_num
			print ('\r[%s]%.2f%%'%(progress(rate),rate*100),end="")
			while threading.activeCount()>thread_num:
				time.sleep(2)
			Get_Question_Thread(q_url,'data/%s/%d.txt'%(name,j+1)).start()

def main():
	## 新建目录	
	makedir('data')
	## 获取所有标签210个 大约3、4秒
	zt_url='http://you.ctrip.com/asks/topics.html'
	tags = get_tags(zt_url,done=1)
	## 根据标签获取问题URL 大约花费20多分钟
	get_q_urls(tags,done=1,thread_num=80)
	## 逐标签进行爬取问题 1个标签大约1分钟
	get_question(tags[:10],thread_num=100)
	## 等待全部线程退出
	t = 0
	while threading.activeCount()>1:
		print ("线程为全部结束，等待 1 秒；还有 %d 个线程"%(threading.activeCount()-1),t)
		time.sleep(1)
		t += 1
		if t>180:
			print ("超时退出")
			break


if __name__ == "__main__":
	main()
