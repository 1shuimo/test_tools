import json
import fitz
import random
import os
import shutil 
import os
import django
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_tools.settings')
django.setup()



# 生成随机填充颜色
def random_fill_color():
    r = random.random()
    g = random.random()
    b = random.random()
    return (r, g, b)

def draw_new_pdf(pdf_path, new_pdf, image_body_info):
    # 确保目标目录存在
    target_dir = os.path.dirname(new_pdf)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # 如果目标PDF文件不存在，复制源PDF到目标路径
    if not os.path.exists(new_pdf):
        shutil.copyfile(pdf_path, new_pdf)
    
    # 打开现有的PDF
    doc = fitz.open(pdf_path)

    # 如果新的PDF已经存在，删除它
    if os.path.exists(new_pdf):
        os.remove(new_pdf)

    # 创建一个新的空白PDF
    new_doc = fitz.open('')   

    for i in range(len(doc)):
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        page = new_doc[-1]
        shape = page.new_shape()
        image_bodys = image_body_info[f'page_idx_{i}']
        if 'inline_equations_bbox' in image_bodys:
            inline_equations_bboxes = image_bodys['inline_equations_bbox']
            for inline_equations_bbox in inline_equations_bboxes:
                x1, y1, x2, y2 = inline_equations_bbox
                line_box = [x1, y1, x2, y2] 
                shape.draw_rect(line_box)
                shape.finish(color=random_fill_color()) 
    
        for key in image_bodys.keys():

            if 'image_body_bbox' in image_bodys[key]:
                x1, y1, x2, y2 = image_bodys[key]['image_body_bbox']
                line_box = [x1, y1, x2, y2] 
                shape.draw_rect(line_box)
                shape.finish(color=random_fill_color())

            elif 'image_caption_bbox' in image_bodys[key]:
                x1, y1, x2, y2 = image_bodys[key]['image_caption_bbox']
                line_box = [x1, y1, x2, y2] 
                shape.draw_rect(line_box)
                shape.finish(color=random_fill_color())

            elif 'table_body_bbox' in image_bodys[key]:
                x1, y1, x2, y2 = image_bodys[key]['table_body_bbox']
                line_box = [x1, y1, x2, y2] 
                shape.draw_rect(line_box)
                shape.finish(color=random_fill_color())  
            
            elif 'table_caption_bbox' in image_bodys[key]:
                x1, y1, x2, y2 = image_bodys[key]['table_caption_bbox']
                line_box = [x1, y1, x2, y2] 
                shape.draw_rect(line_box)
                shape.finish(color=random_fill_color()) 
            
            elif 'table_footnote_bbox' in image_bodys[key]:
                x1, y1, x2, y2 = image_bodys[key]['table_footnote_bbox']
                line_box = [x1, y1, x2, y2] 
                shape.draw_rect(line_box)
                shape.finish(color=random_fill_color())

            elif 'text_bbox' in image_bodys[key]:
                x1, y1, x2, y2 = image_bodys[key]['text_bbox']
                line_box = [x1, y1, x2, y2] 
                shape.draw_rect(line_box)
                shape.finish(color=random_fill_color())

            elif 'title_bbox' in image_bodys[key]:
                x1, y1, x2, y2 = image_bodys[key]['title_bbox']
                line_box = [x1, y1, x2, y2] 
                shape.draw_rect(line_box)
                shape.finish(color=random_fill_color())

            elif 'interline_equations_bbox' in image_bodys[key]:
                x1, y1, x2, y2 = image_bodys[key]['interline_equations_bbox']
                line_box = [x1, y1, x2, y2] 
                shape.draw_rect(line_box)
                shape.finish(color=random_fill_color())
            
            elif 'discarded_bbox' in image_bodys[key]:
                x1, y1, x2, y2 = image_bodys[key]['discarded_bbox']
                line_box = [x1, y1, x2, y2] 
                shape.draw_rect(line_box)
                shape.finish(color=random_fill_color())



        
        # 提交完成的画框
        shape.commit()

    # 保存所做的更改
    new_doc.save(new_pdf)


# 创建一个新的pdf,并将其中所需内容编号
def layout_sort_new_pdf(pdf_path, new_pdf, image_body_info):

    # 打开现有的PDF
    doc = fitz.open(pdf_path)

    # 如果新的PDF已经存在，删除它
    if os.path.exists(new_pdf):
        os.remove(new_pdf)

    # 创建一个新的空白PDF
    new_doc = fitz.open('')   

    for i in range(len(doc)):
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        page = new_doc[-1]
        shape = page.new_shape()
        image_bodys = image_body_info[f'page_idx_{i}']

        for j, key in enumerate(image_bodys.keys()):
            x1, y1, x2, y2 = image_bodys[key]['t_bbox']
            line_box = [x1, y1, x2, y2] 
            shape.draw_rect(line_box)
            shape.finish(color=random_fill_color())

            # 在左上角添加编号
            shape.insert_text((x1, y1), str(j+1), fontsize=12, color=(1, 0, 0))
    
            # 提交完成的画框
        shape.commit()

    # 保存所做的更改
    new_doc.save(new_pdf)

                
def call_annotation_script(raw_pdf_path, json_path):
    # 你的脚本逻辑放在这里，使用raw_pdf_path和json_path进行处理
    with open(json_path, 'r', encoding='utf-8') as f:
        pdf_info = json.load(f)


    # 将处理结果保存到static文件夹中
    base_static_path = settings.STATICFILES_DIRS[0]
    new_pdf_images_body = os.path.join(base_static_path, 'docs', 'show_images_info', 'images_body.pdf')
    new_pdf_images_caption = os.path.join(base_static_path, 'docs', 'show_images_info', 'images_caption.pdf')
    new_pdf_tables_body = os.path.join(base_static_path, 'docs', 'show_tables_info', 'tables_body.pdf')
    new_pdf_tables_caption = os.path.join(base_static_path, 'docs', 'show_tables_info', 'tables_caption.pdf')
    new_pdf_tables_footnote = os.path.join(base_static_path, 'docs', 'show_tables_info', 'tables_footnote.pdf')
    new_pdf_text = os.path.join(base_static_path, 'docs', 'show_para_info', 'text.pdf')
    new_pdf_title = os.path.join(base_static_path, 'docs', 'show_para_info', 'title.pdf')
    new_pdf_layout_sort_para = os.path.join(base_static_path, 'docs', 'show_para_info', 'para_sort.pdf')
    new_pdf_interline_equations = os.path.join(base_static_path, 'docs', 'show_equation_info', 'interline_equations.pdf')
    new_pdf_inline_equations = os.path.join(base_static_path, 'docs', 'show_equation_info', 'inline_equations.pdf')
    new_pdf_discarded_bbox = os.path.join(base_static_path, 'docs', 'show_discarded_info', 'discarded.pdf')

    file_paths = {
        'image_body_info': os.path.join(base_static_path, 'docs', 'show_images_info', 'images_body.json'),
        'image_caption_info': os.path.join(base_static_path, 'docs', 'show_images_info', 'images_caption.json'),
        'table_body_info': os.path.join(base_static_path, 'docs', 'show_tables_info', 'tables_body.json'),
        'table_caption_info': os.path.join(base_static_path, 'docs', 'show_tables_info', 'tables_caption.json'),
        'table_footnote_info': os.path.join(base_static_path, 'docs', 'show_tables_info', 'tables_footnote.json'),
        'text_info': os.path.join(base_static_path, 'docs', 'show_para_info', 'text.json'),
        'title_info': os.path.join(base_static_path, 'docs', 'show_para_info', 'title.json'),
        'text_and_title_info': os.path.join(base_static_path, 'docs', 'show_para_info', 'para_sort.json'),
        'interline_equations_info': os.path.join(base_static_path, 'docs', 'show_equation_info', 'interline_equations.json'),
        'inline_equations_info': os.path.join(base_static_path, 'docs', 'show_equation_info', 'inline_equations.json'),
        'discarded_info': os.path.join(base_static_path, 'docs', 'show_discarded_info', 'discarded.json')
    }
    
    # 用于存储后面所需信息
    image_body_info = {}
    image_caption_info = {}
    table_body_info = {}
    table_caption_info = {}
    table_footnote_info = {}
    text_info = {}
    title_info = {}
    text_and_title_info = {}
    interline_equations_info = {}
    discarded_info = {}
    inline_equations_info = {}

    pdf_all_pages = pdf_info['pdf_info']
    for i, pdf_info_single_page in enumerate(pdf_all_pages):
        image_body_info[f'page_idx_{i}'] = {}
        image_caption_info[f'page_idx_{i}'] = {}
        table_body_info[f'page_idx_{i}'] = {}
        table_caption_info[f'page_idx_{i}'] = {}
        table_footnote_info[f'page_idx_{i}'] = {}
        text_info[f'page_idx_{i}'] = {}
        title_info[f'page_idx_{i}'] = {}
        text_and_title_info[f'page_idx_{i}'] = {}
        interline_equations_info[f'page_idx_{i}'] = {}
        inline_equations_info[f'page_idx_{i}'] = {}
        discarded_info[f'page_idx_{i}'] = {}
        # image_body_info = pdf_info_single_page['page_idx']
        inline_equations_info[f'page_idx_{i}']['inline_equations_bbox'] = []
        inline_equations_info[f'page_idx_{i}']['inline_equations'] = []



        # 若是不为空则获取images信息
        if pdf_info_single_page['images']:
            for j, single_image in enumerate(pdf_info_single_page['images']):
                image_body_info[f'page_idx_{i}'][f'image_{j}'] = {}
                image_caption_info[f'page_idx_{i}'][f'image_{j}'] = {}
                image_body_info[f'page_idx_{i}'][f'image_{j}']['image_bbox'] = single_image['bbox']
                image_caption_info[f'page_idx_{i}'][f'image_{j}']['image_bbox'] = single_image['bbox']
                

                for block in single_image['blocks']:
                    if block['type'] == 'image_body':
                        image_body_info[f'page_idx_{i}'][f'image_{j}']['image_path'] = block['lines'][0]['spans'][0]['image_path']
                        image_body_info[f'page_idx_{i}'][f'image_{j}']['image_body_bbox'] = block['bbox']

                    elif block['type'] == 'image_caption':
                        image_caption_info[f'page_idx_{i}'][f'image_{j}']['image_lines_info'] = block['lines']  # TODO 不知道要如何细分公式和文本，未细分，存到了lines下的所有信息
                        image_caption_info[f'page_idx_{i}'][f'image_{j}']['image_caption_bbox'] = block['bbox']
                        image_caption_info[f'page_idx_{i}'][f'image_{j}']['image_lines_inline_equations'] = {}
                        image_caption_info[f'page_idx_{i}'][f'image_{j}']['image_lines_inline_equations']['inline_equation'] = []
                        image_caption_info[f'page_idx_{i}'][f'image_{j}']['image_lines_inline_equations']['inline_equation_bbox'] = [] 

                        for signle_line in block['lines']:
                            for span in signle_line['spans']:
                                if span['type'] == 'inline_equation':
                                    image_caption_info[f'page_idx_{i}'][f'image_{j}']['image_lines_inline_equations']['inline_equation'].append(span['content'])
                                    image_caption_info[f'page_idx_{i}'][f'image_{j}']['image_lines_inline_equations']['inline_equation_bbox'].append(span['bbox']) 
                                    inline_equations_info[f'page_idx_{i}']['inline_equations_bbox'].append(span['bbox']) 
                                    inline_equations_info[f'page_idx_{i}']['inline_equations'].append(span['content'])

                                    
        # 若是不为空则获取tables信息
        if pdf_info_single_page['tables']:
            for j, single_table in enumerate(pdf_info_single_page['tables']):
                table_body_info[f'page_idx_{i}'][f'table_{j}'] = {}
                table_caption_info[f'page_idx_{i}'][f'table_{j}'] = {}
                table_footnote_info[f'page_idx_{i}'][f'table_{j}'] = {}
                table_body_info[f'page_idx_{i}'][f'table_{j}']['table_bbox'] = single_table['bbox']
                table_caption_info[f'page_idx_{i}'][f'table_{j}']['table_bbox'] = single_table['bbox']
                table_footnote_info[f'page_idx_{i}'][f'table_{j}']['table_bbox'] = single_table['bbox']

                for block in single_table['blocks']:
                    if block['type'] == 'table_body':
                        table_body_info[f'page_idx_{i}'][f'table_{j}']['image_path'] = block['lines'][0]['spans'][0]['image_path']
                        table_body_info[f'page_idx_{i}'][f'table_{j}']['table_body_bbox'] = block['bbox']

                    elif block['type'] == 'table_caption':
                        table_caption_info[f'page_idx_{i}'][f'table_{j}']['table_caption_info'] = block['lines']  # TODO 不知道要如何细分公式和文本，未细分，存到了lines下的所有信息
                        table_caption_info[f'page_idx_{i}'][f'table_{j}']['table_caption_bbox'] = block['bbox']
                        table_caption_info[f'page_idx_{i}'][f'table_{j}']['table_lines_inline_equations'] = {}
                        table_caption_info[f'page_idx_{i}'][f'table_{j}']['table_lines_inline_equations']['inline_equation'] = []
                        table_caption_info[f'page_idx_{i}'][f'table_{j}']['table_lines_inline_equations']['inline_equation_bbox'] = []
                        for signle_line in block['lines']:
                            for span in signle_line['spans']:
                                if span['type'] == 'inline_equation':
                                    table_caption_info[f'page_idx_{i}'][f'table_{j}']['table_lines_inline_equations']['inline_equation'] = span['content']
                                    table_caption_info[f'page_idx_{i}'][f'table_{j}']['table_lines_inline_equations']['inline_equation_bbox'] = span['bbox'] 
                                    inline_equations_info[f'page_idx_{i}']['inline_equations_bbox'].append(span['bbox']) 
                                    inline_equations_info[f'page_idx_{i}']['inline_equations'].append(span['content']) 
                
                    elif block['type'] == 'table_footnote':
                        table_footnote_info[f'page_idx_{i}'][f'table_{j}']['table_footnote_info'] = block['lines']  # TODO 不知道要如何细分公式和文本，未细分，存到了lines下的所有信息
                        table_footnote_info[f'page_idx_{i}'][f'table_{j}']['table_footnote_bbox'] = block['bbox']
                        table_footnote_info[f'page_idx_{i}'][f'table_{j}']['table_lines_inline_equations'] = {}
                        table_footnote_info[f'page_idx_{i}'][f'table_{j}']['table_lines_inline_equations']['inline_equation'] = []
                        table_footnote_info[f'page_idx_{i}'][f'table_{j}']['table_lines_inline_equations']['inline_equation_bbox'] = []
                        for signle_line in block['lines']:
                            for span in signle_line['spans']:
                                if span['type'] == 'inline_equation':
                                    table_footnote_info[f'page_idx_{i}'][f'table_{j}']['table_lines_inline_equations']['inline_equation'] = span['content']
                                    table_footnote_info[f'page_idx_{i}'][f'table_{j}']['table_lines_inline_equations']['inline_equation_bbox'] = span['bbox']  
                                    inline_equations_info[f'page_idx_{i}']['inline_equations_bbox'].append(span['bbox']) 
                                    inline_equations_info[f'page_idx_{i}']['inline_equations'].append(span['content'])
                
        
        # 若是不为空则获取interline_equations信息
        if pdf_info_single_page['interline_equations']:
            for j, single_inter_equation in enumerate(pdf_info_single_page['interline_equations']):
                interline_equations_info[f'page_idx_{i}'][f'interline_equations_{j}'] = {}
                interline_equations_info[f'page_idx_{i}'][f'interline_equations_{j}']['interline_equations_bbox'] = single_inter_equation['bbox']
                interline_equations_info[f'page_idx_{i}'][f'interline_equations_{j}']['interline_equations_content'] = single_inter_equation['lines'][0]['spans'][0]['content'] 
            
        # 若是不为空则获取discarded_blocks信息
        if pdf_info_single_page['discarded_blocks']:
            for j, discarded_bbox in enumerate(pdf_info_single_page['discarded_blocks']):
                discarded_info[f'page_idx_{i}'][f'discarded_{j}'] = {}
                discarded_info[f'page_idx_{i}'][f'discarded_{j}']['discarded_bbox'] = discarded_bbox['bbox'] 

        # 若是不为空则获取para_blocks信息
        if pdf_info_single_page['para_blocks']:
            for j, single_t in enumerate(pdf_info_single_page['para_blocks']):
                text_info[f'page_idx_{i}'][f'text_{j}'] = {}
                title_info[f'page_idx_{i}'][f'title_{j}'] = {}
                text_and_title_info[f'page_idx_{i}'][f't_{j}'] = {}
                text_and_title_info[f'page_idx_{i}'][f't_{j}']['t_bbox'] = single_t['bbox']
                if single_t['type'] == 'text':
                    text_info[f'page_idx_{i}'][f'text_{j}']['text_bbox'] = single_t['bbox']
                    text_info[f'page_idx_{i}'][f'text_{j}']['text_content'] = ''
                    for text_line in single_t['lines']:
                        for text_span in text_line['spans']:
                            text_info[f'page_idx_{i}'][f'text_{j}']['text_content'] += ' ' + text_span['content'] 
                            if text_span['type'] == 'inline_equation':
                                inline_equations_info[f'page_idx_{i}']['inline_equations_bbox'].append(text_span['bbox']) 
                                inline_equations_info[f'page_idx_{i}']['inline_equations'].append(text_span['content'])

                elif single_t['type'] == 'title':
                    title_info[f'page_idx_{i}'][f'title_{j}']['title_bbox'] = single_t['bbox']
                    title_info[f'page_idx_{i}'][f'title_{j}']['title_text_content'] = ''
                    for title_line in single_t['lines']:
                        for title_span in title_line['spans']:
                            title_info[f'page_idx_{i}'][f'title_{j}']['title_text_content'] += title_span['content']
                            if title_span['type'] == 'inline_equation':
                                inline_equations_info[f'page_idx_{i}']['inline_equations_bbox'].append(title_span['bbox']) 
                                inline_equations_info[f'page_idx_{i}']['inline_equations'].append(title_span['content'])



    for directory in file_paths.values():
        directory = os.path.dirname(directory)
        if not os.path.exists(directory):
            os.makedirs(directory)

    for key, file_path in file_paths.items():
        # 使用局部变量名而不是 globals()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(locals()[key], f, ensure_ascii=False, indent=4)

    draw_new_pdf(raw_pdf_path, new_pdf_images_body, image_body_info)
    draw_new_pdf(raw_pdf_path, new_pdf_images_caption, image_caption_info)
    draw_new_pdf(raw_pdf_path, new_pdf_tables_body, table_body_info)
    draw_new_pdf(raw_pdf_path, new_pdf_tables_caption, table_caption_info)
    draw_new_pdf(raw_pdf_path, new_pdf_tables_footnote, table_footnote_info)
    draw_new_pdf(raw_pdf_path, new_pdf_text, text_info)
    draw_new_pdf(raw_pdf_path, new_pdf_title, title_info)
    draw_new_pdf(raw_pdf_path, new_pdf_interline_equations, interline_equations_info)
    layout_sort_new_pdf(raw_pdf_path, new_pdf_layout_sort_para, text_and_title_info)
    draw_new_pdf(raw_pdf_path, new_pdf_discarded_bbox, discarded_info)
    draw_new_pdf(raw_pdf_path, new_pdf_inline_equations, inline_equations_info)

    return {'status': 'success'}








