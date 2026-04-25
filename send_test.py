import requests
with open('test.vcf','rb') as f:
    r = requests.post('http://localhost:8000/analyze', files={'file':('test.vcf',f)}, data={'drug':'Clopidogrel'})
print('status', r.status_code)
print(r.text)
