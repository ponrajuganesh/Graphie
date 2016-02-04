from __future__ import print_function
from flask import request, redirect, url_for, render_template, jsonify
from app import app
from werkzeug import secure_filename
import os
import sys
import pickle


UPLOAD_FOLDER = 'app/files/'
ALLOWED_EXTENSIONS = set(['csv'])
ALLOWED_GRAPHTYPES = ['line', 'pie', 'donut', 'spline', 'area', 'bar', 'gauge', 'sbar']


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		file = request.files['file']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			return render_template('graph.html', filename=filename) 

	return render_template('upload_file.html') 

@app.route('/dumpgraphdata')
def dumpgraphdata():
	filename = request.args.get('filename')
	fp = open(UPLOAD_FOLDER+"/"+filename)
	delimiter = ","
	header = fp.readline()
	header = header.strip()

	result = {}
	colmapper = {}
	count = 0
	cols = []
	
	for col in header.split(delimiter):
		col = col.lower()
		cols.append(col)
		result[col] = []
		colmapper[count] = col
		count += 1

	while 1:
		line = fp.readline()
		
		if not line:
			break
		
		line = line.strip()
		eachline = line.split(delimiter)
		
		for i in range(0, len(eachline)):
			print (result, file=sys.stderr)
			lists = result[colmapper[i]]
			del result[colmapper[i]]
			lists.append(eachline[i])
			result[colmapper[i]] = lists
			
	fp.close()
	
	with open("app/files/data_dump.pik", 'wb') as f:
		pickle.dump(result, f, -1)
	
	return jsonify({"columns": result.keys(), "graphtypes":ALLOWED_GRAPHTYPES})

@app.route('/processgraphsyntax')
def processgraphsyntax():	
	graphsyntax = request.args.get('graphsyntax')
	graphsyntax = graphsyntax.strip()
	ds = None
	with open('app/files/data_dump.pik', 'rb') as f:
		ds = pickle.load(f)
	
	rules = graphsyntax.split(' ')
	graphtype = rules[0]
	graphtype = graphtype.lower()
	result = {}
	
	if graphtype not in ALLOWED_GRAPHTYPES:
		return jsonify({"ferror": "GraphType" + graphtype + " not supported. LINE, PIE, DONUT, SPLINE, AREA are the ones supported"})

	result["graphtype"] = graphtype

	axiscolumn = ""
	columns = []
	for word in rules[1:]:
		word = word.lower()
		cols = word.split(":")
		
		if cols[0] == "base":
			result[cols[1]] = ["x"]
			cols[0] = cols[1]
			axiscolumn = cols[1]
		elif len(cols) == 2:
			result[cols[0]] = [cols[1]]
		else:
			result[cols[0]] = [cols[0]]
		
		lists = []
	
		if cols[0] in ds:
			columns.append(cols[0])
			for val in ds[cols[0]]:
				lists = result[cols[0]]
				lists.append(val)
			
			result[cols[0]] = lists
		else:
			result["error"] = "Column " + cols[0] + " not found in file"
	
	if axiscolumn:
		result["axis"] = result[axiscolumn]
	
	result["columns"] = columns
	result["graphtypes"] = ALLOWED_GRAPHTYPES

	return jsonify(result)

