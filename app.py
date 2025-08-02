import os
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, send_from_directory

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Step 1: Upload CSV
        file = request.files['csv_file']
        if file.filename == '':
            return render_template('index.html', error="No file selected.")

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        df = pd.read_csv(filepath)

        # Step 2: Select Columns
        columns = df.columns.tolist()
        return render_template('index.html', columns=columns, filename=file.filename)

    return render_template('index.html')

@app.route('/plot', methods=['POST'])
def plot():
    x_col = request.form['x_column']
    y_col = request.form['y_column']
    plot_type = request.form['plot_type']
    filename = request.form['filename']

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(filepath)

    x = df[x_col]
    y = df[y_col]

    plt.figure(figsize=(8, 5))
    if plot_type == 'line':
        plt.plot(x, y)
    elif plot_type == 'bar':
        plt.bar(x, y)
    elif plot_type == 'scatter':
        plt.scatter(x, y)

    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f'{plot_type.capitalize()} Plot: {y_col} vs {x_col}')
    plt.tight_layout()
    plot_path = os.path.join(STATIC_FOLDER, 'plot.png')
    plt.savefig(plot_path)
    plt.close()

    preview_x = x.head(10).tolist()
    preview_y = y.head(10).tolist()

    return render_template('index.html', image_file='plot.png', 
                           x_col=x_col, y_col=y_col,
                           preview_x=preview_x, preview_y=preview_y,
                           columns=df.columns.tolist(), filename=filename)

@app.route('/download')
def download_plot():
    return send_from_directory(STATIC_FOLDER, 'plot.png', as_attachment=True)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True)