import os, io, json, time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import openai
import sys
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib

# 加载环境变量（API密钥等）
load_dotenv()
app = Flask(__name__)
CORS(app)  # 允许前端跨域请求

# ==================== 配置 ====================
openai.api_key = os.getenv("DEEPSEEK_API_KEY") 
openai.api_base = "https://api.deepseek.com"

# ==================== 核心业务函数 ====================
sys.path.append('./FrailtyIndex')
from main import ForBackend,validate_input_data,initialize
from cfgs.cfg import BaseConfig

# data_all=pd.read_csv("./data/UKB.csv",sep=",")
args = BaseConfig()
args = args.initialize()
args.groups=45
args.cont=32
args.cate=11
gpu_id=1
output_path="./output/"

def predict_frailty_index_43(data_df,fileID,args,mode=43,gpu_id=1):
    args=initialize(args,mode,gpu_id)
    validate_input_data(data_df,args.cont,args.cate) # 没有检查缺失的列
    res_df=ForBackend(data_df,args)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    res_df.to_csv(output_path+fileID+".csv")
    return res_df


matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

def survival_analysis(data_df,file_id,):

    return
    

def generate_distribution_plot(data_df, filID,save_dir="./plots"):
    os.makedirs(save_dir, exist_ok=True)
    result = {
        "record_count": len(data_df),
        "image_path": None,
        "message": ""
    }
    
    try:
        if len(data_df) == 1:
            result["message"] = "只有一行记录，生成参考分布图并标注当前值"
            ref_file_path = "0.727_test.csv"
            try:
                ref_df = pd.read_csv(ref_file_path)
            except Exception as e:
                result["message"] = f"读取参考文件失败: {str(e)}"
                return result
            current_bcdfi = data_df['BCDFI'].iloc[0]
            plt.figure(figsize=(12, 8))
            sns.histplot(ref_df['pred_fi'], kde=True, color='lightblue', 
                        alpha=0.5, label='参考分布', stat='density')
            # plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
            #         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            # 标注当前值的位置
            plt.axvline(x=current_bcdfi, color='red', linestyle='--', linewidth=2, 
                       label=f'当前BCDFI值: {current_bcdfi:.3f}')
            
            # 在当前值位置添加标记点
            plt.scatter([current_bcdfi], [0], color='red', s=100, zorder=5)
            
            # 添加当前值文本标注
            plt.annotate(f'当前值: {current_bcdfi:.3f}', 
                        xy=(current_bcdfi, 0),
                        xytext=(current_bcdfi, plt.ylim()[1] * 0.05),
                        ha='center',
                        arrowprops=dict(arrowstyle='->', color='red'),
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.1))
            
            plt.title('参考数据分布与当前值对比', fontsize=16, fontweight='bold')
            plt.xlabel('值', fontsize=14)
            plt.ylabel('密度', fontsize=14)
            plt.legend(fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # 保存图片
            image_path = os.path.join(save_dir, f"single_record_distribution_{timestamp}.png")
            plt.tight_layout()
            plt.savefig(image_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            result["image_path"] = image_path
            result["current_value"] = float(current_bcdfi)
            result["reference_stats"] = {
                "mean": float(ref_df['pred_fi'].mean()),
                "std": float(ref_df['pred_fi'].std()),
                "median": float(ref_df['pred_fi'].median()),
                "count": int(len(ref_df))
            }
            
        # 情况2：有多条记录
        else:
            result["message"] = f"有多条记录({len(data_df)}条)，生成BCDFI分布图"
            
            # 创建图形
            plt.figure(figsize=(12, 8))
            
            # 绘制BCDFI的分布
            if len(data_df['BCDFI']) > 1:
                # 使用直方图和核密度估计
                sns.histplot(data_df['BCDFI'], kde=True, color='lightgreen', 
                           alpha=0.5, label='BCDFI分布', stat='density')
                # mean_val = data_df['BCDFI'].mean()
                # std_val = data_df['BCDFI'].std()
                # median_val = data_df['BCDFI'].median()
                # min_val = data_df['BCDFI'].min()
                # max_val = data_df['BCDFI'].max()
                
                # 添加均值线和中位数线
                plt.axvline(x=mean_val, color='blue', linestyle='--', linewidth=2, 
                          label=f'均值: {mean_val:.3f}')
                plt.axvline(x=median_val, color='orange', linestyle='--', linewidth=2,
                          label=f'中位数: {median_val:.3f}')
                # stats_text = f"数据统计:\n均值: {mean_val:.3f}\n标准差: {std_val:.3f}\n中位数: {median_val:.3f}\n最小值: {min_val:.3f}\n最大值: {max_val:.3f}\n样本数: {len(data_df)}"
                # plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
                #         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            else:
                # 如果只有一条记录但被错误归类到这里，显示单点
                plt.scatter(data_df['BCDFI'], [0], color='green', s=200, label='BCDFI值')
                plt.text(data_df['BCDFI'].iloc[0], 0, f'值: {data_df["BCDFI"].iloc[0]:.3f}', 
                        ha='center', va='bottom')
            
            plt.title('BCDFI值分布', fontsize=16, fontweight='bold')
            plt.xlabel('BCDFI值', fontsize=14)
            plt.ylabel('密度', fontsize=14)
            plt.legend(fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # 保存图片
            image_path = os.path.join(save_dir, f"multiple_records_distribution_{timestamp}.png")
            plt.tight_layout()
            plt.savefig(image_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            result["image_path"] = image_path
            result["stats"] = {
                "mean": float(data_df['BCDFI'].mean()),
                "std": float(data_df['BCDFI'].std()),
                "median": float(data_df['BCDFI'].median()),
                "min": float(data_df['BCDFI'].min()),
                "max": float(data_df['BCDFI'].max()),
                "count": int(len(data_df))
            }
            
        result["success"] = True
        
    except Exception as e:
        result["success"] = False
        result["message"] = f"生成分布图时出错: {str(e)}"
    
    return result

from flask import request, jsonify, send_file
import markdown
import pdfkit
import uuid
import os
import requests
import traceback
from flask_cors import CORS
from weasyprint import HTML
from dotenv import load_dotenv

load_dotenv()  # 这会加载项目根目录的 .env 文件中的变量
app = Flask(__name__)
CORS(app)  
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# 填写你的 API Key
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not API_KEY:
    raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")

url = "https://api.deepseek.com/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json(silent=True) or {}
        print(f"请求体: {data}")

        response = requests.post(
            url,  # 你的AI接口URL
            headers=headers,
            json=data
        )
        print("response: ",response)
        if response.status_code == 200:
            result = response.json()
            res_md = result['choices'][0]['message']['content']
            
            # 保存Markdown文件
            report_id = str(uuid.uuid4())
            md_filename = f"reports/{report_id}.md"
            pdf_filename = f"reports/{report_id}.pdf"

            os.makedirs('reports', exist_ok=True)
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(res_md)

            # 转换为PDF
            # try:
            options = {
                'encoding': 'UTF-8',
                'custom-header': [('Content-Encoding', 'utf-8')],
                'enable-local-file-access': None
            }
            options = {
                'encoding': 'UTF-8',
                'custom-header': [('Content-Encoding', 'utf-8')],
                'enable-local-file-access': None,
                'page-size': 'A4',
                'margin-top': '20mm',
                'margin-right': '20mm',
                'margin-bottom': '20mm',
                'margin-left': '20mm',
            }
            
            # 添加CSS样式
            css = '''
            <style>
            body { font-family: "Microsoft YaHei", sans-serif; }
            h1 { color: #333; border-bottom: 2px solid #007bff; }
            h2 { color: #555; margin-top: 25px; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background-color: #f8f9fa; }
            .disclaimer { color: #dc3545; font-style: italic; }
            </style>
            '''
            
            with open(md_filename, 'r', encoding='utf-8') as f:
                html = markdown.markdown(f.read())
            
            full_html = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        @page {{ size: A4; margin: 20mm; }}
                        body {{ font-family: "Microsoft YaHei", sans-serif; font-size: 12pt; }}
                        h1 {{ color: #333; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; }}
                    </style>
                </head>
                <body>
                    {html}
                </body>
                </html>
                '''

                # 生成PDF
            HTML(string=full_html).write_pdf(pdf_filename)
            # pdfkit.from_string(html, pdf_filename, options=options)
                # html = markdown.markdown(res_md)
                # full_html = f'<!DOCTYPE html><html><head><meta charset="UTF-8">{css}</head><body>{html}</body></html>'
                # pdfkit.from_string(full_html, pdf_filename, options=options)
            
            # except Exception as e:
            #     print(f"PDF转换失败: {e}")
            #     pdf_filename = None
                
            
            return jsonify({
                'success': True,
                'data': {
                    'id': report_id,
                    'markdown': res_md,
                    'pdfUrl': f'/api/reports/{report_id}.pdf' if pdf_filename else None
                }
            }),200
        

    except Exception as e:
        print(f"错误详情: {traceback.format_exc()}")
        return jsonify({"status": "error","error": str(e)}), 500


    #     else:
    #         return jsonify({
    #             'success': False,
    #             'message': f'AI模型请求失败: {response.status_code}'
    #         }), 500
        


@app.route('/api/convert-to-pdf', methods=['POST'])
def convert_to_pdf():
    """
    将Markdown转换为PDF
    """
    try:
        data = request.json
        print("convert pdf:",data)
        content = data.get('markdown')
        filename = data.get('filename', 'report')
        
        if not content:
            return jsonify({'error': '没有提供Markdown内容'}), 400
        
        pdf_filename = f"reports/{data.get('id')}.pdf"
        print("pdf_filename:", pdf_filename)
        # 确保temp目录存在
        os.makedirs('reports', exist_ok=True)
        
        # 转换为PDFKUAK
        options = {
            'encoding': 'UTF-8',
            'custom-header': [('Content-Encoding', 'utf-8')],
            'enable-local-file-access': None,
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
        }
        
        css = '''
        <style>
        body { font-family: "Microsoft YaHei", sans-serif; font-size: 12pt; }
        h1 { color: #333; border-bottom: 2px solid #007bff; }
        h2 { color: #555; margin-top: 25px; }
        table { border-collapse: collapse; width: 100%; margin: 15px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f8f9fa; }
        .disclaimer { color: #dc3545; font-style: italic; }
        </style>
        '''
        
        html = markdown.markdown(markdown_content)
        full_html = f'<!DOCTYPE html><html><head><meta charset="UTF-8">{css}</head><body>{html}</body></html>'
        
        pdfkit.from_string(full_html, pdf_filename, options=options)
        
        return send_file(
            pdf_filename,
            as_attachment=True,
            download_name=f'{filename}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/<report_id>.pdf')
def get_report_pdf(report_id):
    """
    获取PDF报告文件
    """
    pdf_path = f'reports/{report_id}.pdf'
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        return jsonify({'error': '报告不存在'}), 404




# 临时文件存储目录（确保此目录存在）
TEMP_DATA_DIR = './temp_upload_data'
os.makedirs(TEMP_DATA_DIR, exist_ok=True)
# 我们需要一个地方来临时保存每个 file_id 对应的预测结果 DataFrame
# 这里用一个简单的字典在内存中缓存（注意：重启服务会丢失，生产环境建议用Redis或数据库）
prediction_cache = {}

# 临时文件清理函数（可选，定期清理）
def cleanup_old_temp_files(hours=24):
    """清理超过指定小时数的临时文件"""
    current_time = datetime.now()
    for filename in os.listdir(TEMP_DATA_DIR):
        filepath = os.path.join(TEMP_DATA_DIR, filename)
        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if current_time - file_time > timedelta(hours=hours):
                os.remove(filepath)
                print(f"已清理旧临时文件: {filename}")

# # ==================== API路由 ====================

# @app.route('/api/health', methods=['GET'])
# def health_check():
#     return jsonify({'status': 'healthy', 'service': 'Frailty Index API'})
import uuid

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '未上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    try:
        # 支持CSV和Excel
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return jsonify({'error': '仅支持CSV或Excel文件'}), 400
        
        file_id = str(uuid.uuid4())
        temp_filepath = os.path.join(TEMP_DATA_DIR, f'{file_id}.parquet')
        df.to_parquet(temp_filepath, index=False)
        
        cleanup_old_temp_files(hours=24)
        
        # 数据预览（前5行）
        preview = df.head().to_dict(orient='records')
        return jsonify({
            'message': '文件上传成功',
            'file_id':file_id,
            'rows': len(df),
            'columns': list(df.columns),
            'preview': preview,
        })
        
    except Exception as e:
        return jsonify({'error': f'文件解析失败: {str(e)}'}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        if not data or 'file_id' not in data:
            return jsonify({'error': '缺少数据'}), 400

        file_id = data['file_id']
        temp_filepath = os.path.join(TEMP_DATA_DIR, f'{file_id}.parquet')
        if not os.path.exists(temp_filepath):
            return jsonify({'error': '文件已过期或不存在，请重新上传'}), 404
        df = pd.read_parquet(temp_filepath)
        print(f"从临时文件加载数据，形状: {df.shape}")

        frailty_results = predict_frailty_index_43(df,file_id,args)
        # survival_data = survival_analysis(frailty_results,file_id,)
        global prediction_cache
        prediction_cache[file_id]=frailty_results
        return jsonify({
            'frailty': frailty_results.to_dict(orient='records'),
            # 'frailty_distribution': frailty_results['BCDFI'].tolist(),
        })
             # 'survival_curves': survival_data,
            # 'summary': {
            #     'total_patients': len(df),
            #     # 'high_risk_count': frailty_results['risk_level'].count('高风险'),
            #     # 'avg_frailty': np.mean(frailty_results['frailty_index'])
            # }        
    except Exception as e:
        print(f'预测失败: {str(e)}')
        return jsonify({'error': f'预测失败: {str(e)}'}), 500


from flask import make_response
from io import StringIO

@app.route('/api/download', methods=['GET'])
def download_prediction():
    try:
        file_id = request.args.get('file_id')
        if not file_id:
            return jsonify({'error': '缺少 file_id 参数'}), 400
        if file_id not in prediction_cache:
            return jsonify({'error': '预测结果不存在或已过期，请重新预测'}), 404
        
        result_df = prediction_cache[file_id]
        csv_buffer = StringIO()
        result_df.to_csv(csv_buffer, index=False) # index=False 不保存行索引
        csv_str = csv_buffer.getvalue()
        csv_buffer.close()
        
        response = make_response(csv_str)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=frailty_prediction_{file_id}.csv'
        
        return response
        
    except Exception as e:
        print(f'下载失败: {str(e)}')
        return jsonify({'error': f'文件生成失败: {str(e)}'}), 500


import pandas as pd
import uuid
import os

single_csv_dir="single_csv_uploads/"

@app.route('/api/upload-single-csv', methods=['POST'])
def upload_single_csv():
    print("request: ",request.files)
    try:
        # return jsonify({'检测！'}), 400
        # if 'file' not in request.files:
        #     return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'error': '只支持CSV格式文件'}), 400

        try:
            df = pd.read_csv(file)
            print(df)
        except Exception as e:
            return jsonify({'error': f'CSV文件解析失败: {str(e)}'}), 400
        if len(df) == 0:
            return jsonify({'error': 'CSV文件为空'}), 400
        if len(df) > 1:
            return jsonify({'error': '请上传单人记录文件'}), 400
        
        # # 生成文件ID
        file_id = str(uuid.uuid4())
        
        # # 保存文件到临时目录
        os.makedirs(single_csv_dir, exist_ok=True)
        file_path = os.path.join(single_csv_dir, f'{file_id}.csv')
        df.to_csv(file_path, index=False)
        
        # # 准备预览数据
        preview_data = df.values.tolist()
        columns = df.columns.tolist()
        print("preview_data: ",len(preview_data),type(preview_data))
        
        # return jsonify({
        #     'success': True,
        #     'file_id': file_id,
        #     'record_count': len(df),
        #     'columns': columns,
        #     # 'data': preview_data
        # })
        return jsonify({
            'success': True,
            'file_id': file_id,
            'record_count': len(df),
            'columns': columns,
            'data': preview_data
        })
    except Exception as e:
        return jsonify({'error': str(e)+">>>>"}), 500

@app.route('/api/predict-single-csv', methods=['POST'])
def predict_single_csv():
    """
    预测CSV单条记录
    """
    try:
        data = request.json
        
        if 'file_id' not in data:
            return jsonify({'error': '缺少文件ID'}), 400
        
        # 从文件加载数据
        file_path = single_csv_dir+f'{data["file_id"]}.csv'
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        df = pd.read_csv(file_path)
        if len(df) == 0:
            return jsonify({'error': '数据为空'}), 400
        
        # 只取第一条记录
        record = df.iloc[0].to_dict()
        
        # 这里调用你的预测模型
        frailty_results = predict_frailty_index_43(df,data["file_id"],args)

        return jsonify({
            'success': True,
            'data': frailty_results.to_dict(orient='records'),

        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)