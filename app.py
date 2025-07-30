import os
import uuid
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, request, render_template, send_file, redirect, url_for, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATIC_FOLDER'] = 'static'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

def clean_old_files(directory, max_files=5):
    files = [os.path.join(directory, f) for f in os.listdir(directory)]
    if len(files) > max_files:
        files.sort(key=os.path.getmtime)
        for f in files[:-max_files]:
            try:
                os.remove(f)
            except:
                pass

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload
        if 'csv_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['csv_file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
            
        if not allowed_file(file.filename):
            flash('Only CSV files are allowed', 'error')
            return redirect(request.url)
            
        try:
            # Save file
            filename = str(uuid.uuid4()) + '.csv'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Read CSV
            df = pd.read_csv(filepath)
            columns = df.columns.tolist()
            
            # Clean old files
            clean_old_files(app.config['UPLOAD_FOLDER'])
            
            return render_template('index.html', 
                                 columns=columns, 
                                 filename=filename,
                                 data_preview=df.head(10).to_html(classes='table table-striped'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(request.url)
    
    # Handle plot generation
    plot_filename = request.args.get('plot')
    filename = request.args.get('filename')
    
    if plot_filename:
        return render_template('index.html', plot=plot_filename)
    
    if filename:
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            df = pd.read_csv(filepath)
            columns = df.columns.tolist()
            return render_template('index.html', 
                                 columns=columns, 
                                 filename=filename,
                                 data_preview=df.head(10).to_html(classes='table table-striped'))
        except:
            pass
    
    return render_template('index.html')

@app.route('/plot', methods=['POST'])
def plot():
    try:
        filename = request.form['filename']
        x_col = request.form['x_column']
        y_col = request.form['y_column']
        plot_type = request.form['plot_type']
        title = request.form.get('title', f'{y_col} vs {x_col}')
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(filepath)
        
        # Create plot
        plt.figure(figsize=(10, 6))
        
        if plot_type == 'line':
            plt.plot(df[x_col], df[y_col], marker='o', linestyle='-', color='blue')
        elif plot_type == 'bar':
            plt.bar(df[x_col], df[y_col], color='green')
        elif plot_type == 'scatter':
            plt.scatter(df[x_col], df[y_col], color='red')
        elif plot_type == 'pie':
            plt.pie(df[y_col], labels=df[x_col], autopct='%1.1f%%')
        
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.title(title)
        plt.grid(True)
        plt.tight_layout()
        
        # Save plot
        plot_filename = f"plot_{uuid.uuid4().hex}.png"
        plot_path = os.path.join(app.config['STATIC_FOLDER'], plot_filename)
        plt.savefig(plot_path)
        plt.close()
        
        clean_old_files(app.config['STATIC_FOLDER'])
        
        return redirect(url_for('index', plot=plot_filename, filename=filename))
    
    except Exception as e:
        flash(f'Error generating plot: {str(e)}', 'error')
        return redirect(url_for('index', filename=filename))

@app.route('/download/<plot_filename>')
def download(plot_filename):
    plot_path = os.path.join(app.config['STATIC_FOLDER'], plot_filename)
    return send_file(plot_path, as_attachment=True)

@app.route('/reset')
def reset():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)