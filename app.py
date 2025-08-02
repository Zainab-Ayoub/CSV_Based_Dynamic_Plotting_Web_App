import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import io
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configuration
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'csv'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_numeric_columns(df):
    """Get numeric columns from dataframe"""
    return df.select_dtypes(include=['number']).columns.tolist()

def get_categorical_columns(df):
    """Get categorical/text columns from dataframe"""
    return df.select_dtypes(include=['object', 'category']).columns.tolist()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Read and validate CSV
            df = pd.read_csv(filepath)
            
            if df.empty:
                flash('The uploaded CSV file is empty')
                return redirect(url_for('index'))
            
            # Get column information
            all_columns = df.columns.tolist()
            numeric_columns = get_numeric_columns(df)
            categorical_columns = get_categorical_columns(df)
            
            # Store filename in session-like manner (for demo, using simple approach)
            return render_template('index.html', 
                                 filename=filename,
                                 columns=all_columns,
                                 numeric_columns=numeric_columns,
                                 categorical_columns=categorical_columns,
                                 data_preview=df.head(10).to_html(classes='table table-striped table-sm'),
                                 total_rows=len(df))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload a CSV file.')
        return redirect(url_for('index'))

@app.route('/plot', methods=['POST'])
def create_plot():
    try:
        filename = request.form.get('filename')
        x_column = request.form.get('x_column')
        y_column = request.form.get('y_column')
        plot_type = request.form.get('plot_type')
        
        if not all([filename, x_column, y_column, plot_type]):
            flash('Please fill in all required fields')
            return redirect(url_for('index'))
        
        # Read the CSV file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(filepath)
        
        # Create the plot
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Handle different plot types
        if plot_type == 'line':
            ax.plot(df[x_column], df[y_column], marker='o', linewidth=2, markersize=6)
            ax.set_title(f'Line Plot: {y_column} vs {x_column}', fontsize=14, fontweight='bold')
            
        elif plot_type == 'bar':
            # For bar plots, if x is categorical, use it directly
            # If x is numeric, we might want to group or sample
            if df[x_column].dtype == 'object' or len(df[x_column].unique()) < 20:
                # Group by x_column and sum y_column for categorical or small numeric data
                grouped_data = df.groupby(x_column)[y_column].sum().reset_index()
                ax.bar(grouped_data[x_column], grouped_data[y_column], alpha=0.7, color='skyblue', edgecolor='navy')
                plt.xticks(rotation=45)
            else:
                # For large numeric x data, create bins
                ax.hist(df[x_column], bins=20, alpha=0.7, color='skyblue', edgecolor='navy')
                ax.set_ylabel('Frequency')
            ax.set_title(f'Bar Plot: {y_column} vs {x_column}', fontsize=14, fontweight='bold')
            
        elif plot_type == 'scatter':
            ax.scatter(df[x_column], df[y_column], alpha=0.6, s=60, color='coral', edgecolors='darkred')
            ax.set_title(f'Scatter Plot: {y_column} vs {x_column}', fontsize=14, fontweight='bold')
            
        elif plot_type == 'histogram':
            ax.hist(df[y_column], bins=20, alpha=0.7, color='lightgreen', edgecolor='darkgreen')
            ax.set_xlabel(y_column)
            ax.set_ylabel('Frequency')
            ax.set_title(f'Histogram: {y_column}', fontsize=14, fontweight='bold')
            
        elif plot_type == 'box':
            if df[x_column].dtype == 'object':
                # Box plot by category
                categories = df[x_column].unique()
                data_to_plot = [df[df[x_column] == cat][y_column].dropna() for cat in categories]
                ax.boxplot(data_to_plot, labels=categories)
                plt.xticks(rotation=45)
            else:
                # Simple box plot of y column
                ax.boxplot(df[y_column].dropna())
                ax.set_xticklabels([y_column])
            ax.set_title(f'Box Plot: {y_column} vs {x_column}', fontsize=14, fontweight='bold')
        
        # Set labels
        ax.set_xlabel(x_column, fontsize=12)
        ax.set_ylabel(y_column, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(STATIC_FOLDER, 'plot.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Get column information for the form
        all_columns = df.columns.tolist()
        numeric_columns = get_numeric_columns(df)
        categorical_columns = get_categorical_columns(df)
        
        # Get preview data for selected columns
        preview_data = df[[x_column, y_column]].head(10)
        
        return render_template('index.html',
                             filename=filename,
                             columns=all_columns,
                             numeric_columns=numeric_columns,
                             categorical_columns=categorical_columns,
                             plot_created=True,
                             selected_x=x_column,
                             selected_y=y_column,
                             selected_plot_type=plot_type,
                             data_preview=df.head(10).to_html(classes='table table-striped table-sm'),
                             preview_data=preview_data.to_html(classes='table table-striped table-sm'),
                             total_rows=len(df))
    
    except Exception as e:
        flash(f'Error creating plot: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download_plot')
def download_plot():
    """Download the generated plot"""
    try:
        plot_path = os.path.join(STATIC_FOLDER, 'plot.png')
        if os.path.exists(plot_path):
            return send_file(plot_path, as_attachment=True, download_name='data_visualization.png')
        else:
            flash('No plot available for download')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error downloading plot: {str(e)}')
        return redirect(url_for('index'))

@app.route('/reset')
def reset():
    """Reset the application - clear uploaded files and plots"""
    try:
        # Clean up uploaded files (optional - you might want to keep them)
        # for filename in os.listdir(UPLOAD_FOLDER):
        #     os.remove(os.path.join(UPLOAD_FOLDER, filename))
        
        # Remove the current plot
        plot_path = os.path.join(STATIC_FOLDER, 'plot.png')
        if os.path.exists(plot_path):
            os.remove(plot_path)
            
        flash('Application reset successfully')
    except Exception as e:
        flash(f'Error during reset: {str(e)}')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)