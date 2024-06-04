from django.shortcuts import render, get_object_or_404
import shutil
from django.http import JsonResponse
from django.conf import settings
import json
import os
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from adjust_bbox_mask import call_annotation_script
from django.db.models import Count, Q
from .models import PDFPageDataItem
from django.db import transaction, connection
from urllib.parse import unquote

LABEL_MAPPING = {
    "通过": "label_1",
    "不通过": "label_2",
    "图片、表格Caption混入": "label_3",
    "行内公式缺失": "label_4",
    "行内公式转换错误": "label_5",
    "行间公式转换错误": "label_6",
    "阅读顺序错误": "label_7",
    "页眉、页脚、边注、footnote混入正文": "label_8",
    "文本分段错误": "label_9",
    "抽取内容不完整": "label_10"
}

def home(request):
    return render(request, 'home.html')

def label_stats(request):
    return render(request, 'label_stats.html')

current_file_index = 0
pdf_files = []

@csrf_exempt
def process_folder(request):
    global pdf_files, current_file_index, folder_path
    if request.method == 'POST':
        data = json.loads(request.body)
        folder_path = data['folderPath']
        json_file_path = os.path.join(folder_path, 'pdf_files.json')
        
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                pdf_files = json.load(f)
                for item in pdf_files:
                    filename = item['file_name']
                    num_pages = item.get('num_pages', 1)
                    for page_number in range(1, num_pages + 1):
                        if not PDFPageDataItem.objects.filter(filename=filename, page_number=page_number).exists():
                            PDFPageDataItem.objects.create(
                                filename=filename,
                                page_number=page_number,
                                **{LABEL_MAPPING[key]: False for key in LABEL_MAPPING}
                            )
            current_file_index = 0
            return JsonResponse({'status': 'success', 'pdf_files': pdf_files})
        else:
            return JsonResponse({'status': 'fail', 'message': 'pdf_files.json not found'})
    return JsonResponse({'status': 'fail'})

def clear_static_folders():
    static_folders = [
        'myapp/static/docs/show_images_info',
        'myapp/static/docs/show_tables_info',
        'myapp/static/docs/show_para_info',
        'myapp/static/docs/show_equation_info',
        'myapp/static/docs/show_discarded_info',
        'myapp/static/images'
    ]
    for folder in static_folders:
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder)

@csrf_exempt
def process_pdf(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        filename = data.get('filename')
        if not filename:
            return JsonResponse({'status': 'fail', 'message': 'Filename not provided'}, status=400)

        result = process_single_pdf(filename)
        return JsonResponse(result)
    else:
        return JsonResponse({'status': 'fail', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def get_label_stats(request):
    if request.method == "GET":
        label_stats = PDFPageDataItem.objects.aggregate(
            **{f'{LABEL_MAPPING[key]}_count': Count(LABEL_MAPPING[key], filter=Q(**{LABEL_MAPPING[key]: True})) for key in LABEL_MAPPING}
        )
        return JsonResponse({'status': 'success', 'label_stats': label_stats})
    return JsonResponse({'status': 'fail', 'message': 'Invalid request method'})



@csrf_exempt
@transaction.atomic
def save_labels_bulk(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            labels = data['labels']
            PDFPageDataItem.objects.bulk_create([
                PDFPageDataItem(
                    filename=label['filename'],
                    page_number=label['page_number'],
                    **{LABEL_MAPPING[key]: label.get(key, False) for key in LABEL_MAPPING}
                ) for label in labels
            ], ignore_conflicts=True)
            return JsonResponse({'status': 'success'})
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        finally:
            connection.close()
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    
@csrf_exempt
def get_page_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        filename = data['filename']
        page_number = data['page_number']

        try:
            page_data = PDFPageDataItem.objects.get(filename=filename, page_number=page_number)
            formatted_data = {
                'page_number': page_data.page_number,
                'labels': {key: getattr(page_data, LABEL_MAPPING[key]) for key in LABEL_MAPPING}
            }
            return JsonResponse({'status': 'success', 'data': formatted_data})
        except PDFPageDataItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Page data not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@csrf_exempt
def annotate_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            page_number = data.get('page_number')
            label = data.get('label')
            label = unquote(label) # 对标签进行URL解码


            print(f"Received data: item_id={item_id}, page_number={page_number}, label={label}")

            if not item_id or not page_number or not label:
                print("Missing required fields")
                return JsonResponse({'status': 'fail', 'message': '缺少 item_id, page_number, 或 label'}, status=400)

            if label in LABEL_MAPPING:
                print(f"Label is valid: {label}")
                pdf_page_data_item, created = PDFPageDataItem.objects.get_or_create(filename=item_id, page_number=page_number)
                
                label_field = LABEL_MAPPING[label]
                current_status = getattr(pdf_page_data_item, label_field, False)
                new_status = not current_status
                setattr(pdf_page_data_item, label_field, new_status)
                pdf_page_data_item.save()

                action = 'added' if new_status else 'removed'
                print(f"Annotation {action}: {label}")
                return JsonResponse({'status': 'success', 'message': f'标注 {action}', 'action': action, 'label': label})
            else:
                print(f"Invalid label: {label}")
                return JsonResponse({'status': 'fail', 'message': 'Invalid label'}, status=400)
        except json.JSONDecodeError:
            print("Invalid JSON format")
            return JsonResponse({'status': 'fail', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({'status': 'fail', 'message': str(e)}, status=500)
    else:
        print("Invalid request method")
        return JsonResponse({'status': 'fail', 'message': '无效的请求方法'}, status=405)
    

@csrf_exempt
def get_annotation_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        filename = data['item_id']
        page_number = data['page_number']

        try:
            page_data = PDFPageDataItem.objects.get(filename=filename, page_number=page_number)
            labels_status = {key: getattr(page_data, LABEL_MAPPING[key]) for key in LABEL_MAPPING}
            return JsonResponse({'status': 'success', 'labels': labels_status})
        except PDFPageDataItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Page data not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    
def process_single_pdf(filename):
    global folder_path
    raw_pdf_path = os.path.join(folder_path, f'raw-pdf/{filename}.pdf')
    json_path = os.path.join(folder_path, f'{filename}/auto/{filename}.json')
    
    # 调试信息，打印路径
    print(f"JSON Path: {json_path}")
    
    # 检查 JSON 文件是否存在
    if not os.path.exists(json_path):
        print(f"JSON file not found: {json_path}")
        return {'status': 'fail', 'message': f'JSON file not found: {json_path}'}
    
    # 读取 JSON 文件内容
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # print(f"JSON content: {data}")
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return {'status': 'fail', 'message': f'Error reading JSON file: {e}'}
     # 清空 static 文件夹
    
    clear_static_folders()

    # 将 images 文件夹复制到 Django 静态目录
    src_images_path = os.path.join(folder_path, f'{filename}/auto/images')
    dest_images_path = os.path.join('myapp/static/images')
    if os.path.exists(dest_images_path):
        shutil.rmtree(dest_images_path)
    shutil.copytree(src_images_path, dest_images_path)

    
        
    # 调用处理脚本
    call_annotation_script(raw_pdf_path, json_path)

    return {'status': 'success', 'message': 'PDF processed successfully'}


def get_pdf_at_index(request, index):
    """ Helper function to process and respond with PDF details at a given index """
    global pdf_files
    if 0 <= index < len(pdf_files):
        filename = pdf_files[index].get('file_name')
        result = process_single_pdf(filename)  # 直接调用处理文件的函数
        return JsonResponse({'status': 'success', 'filename': filename, 'result': result})
    return JsonResponse({'status': 'fail', 'message': 'Index out of range'})

def get_current_pdf(request):
    return get_pdf_at_index(request, current_file_index)

def next_pdf(request):
    global current_file_index, pdf_files
    if current_file_index < len(pdf_files) - 1:
        current_file_index += 1
        return get_pdf_at_index(request, current_file_index)
    return JsonResponse({'status': 'fail', 'message': 'Already at last PDF'})

def prev_pdf(request):
    global current_file_index, pdf_files
    if current_file_index > 0:
        current_file_index -= 1
        return get_pdf_at_index(request, current_file_index)
    return JsonResponse({'status': 'fail', 'message': 'Already at first PDF'})


def export_json(request):
    if request.method == 'GET':
        all_data = PDFPageDataItem.objects.all()
        export_data = {}

        for item in all_data:
            if item.filename not in export_data:
                export_data[item.filename] = {}
            if item.page_number not in export_data[item.filename]:
                export_data[item.filename][item.page_number] = {
                    key: getattr(item, LABEL_MAPPING[key]) for key in LABEL_MAPPING
                }

        response = HttpResponse(json.dumps(export_data, indent=4, ensure_ascii=False), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="page_data.json"'
        return response

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def load_json_data(request):
    # 从请求中获取文件路径参数
    relative_path = request.GET.get('path')
    if relative_path:
        # 构建正确的文件系统路径
        # 假设 JSON 文件实际存放在 'myapp/static/docs/show_images_info/' 目录
        json_file_path = os.path.join(settings.BASE_DIR, 'myapp/static', relative_path.strip('/'))
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return JsonResponse(data)
        except FileNotFoundError:
            return JsonResponse({'error': '文件未找到'}, status=404)
    else:
        return JsonResponse({'error': '未提供文件路径'}, status=400)