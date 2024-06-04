// File path: static/pdf_viewer.js
const pdfjsLib = window['pdfjsLib'];

pdfjsLib.GlobalWorkerOptions.workerSrc = './pdf.worker.mjs';
var pdfDoc = null;
var pageNum = 1;
var pageRendering = false;
var pageNumPending = null;
var scale = 1.5;
var canvas = document.getElementById('the-canvas');
var ctx = canvas.getContext('2d');
var currentImageData = null;
var currentFormulaData= null;
var currentTextData= null;

const DISPLAY_TYPES = {
    NONE: 'none',
    IMAGES: 'image_body_bbox',
    TABLES: 'table_body_bbox',
    INLINE_FORMULAS: 'inline_equations',
    INTERLINE_FORMULAS: 'interline_equations',
    TEXT: 'text_bbox',
};

var currentDisplayType = DISPLAY_TYPES.NONE;  // 默认不显示特定内容


const labelMapping = {
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
};


function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// 从前端获取文件路径读取pdf
document.getElementById('folderForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const folderPath = document.getElementById('folderPath').value;
    fetch('/process_folder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ folderPath: folderPath }),
    }).then(response => response.json()).then(data => {
        if (data.status === 'success') {
            console.log(data.pdf_files);
            // 获取第一个PDF文件名
            const firstFilename = data.pdf_files[0].file_name;
            // 立即处理第一个PDF文件
            processPdf(firstFilename);
            document.getElementById('item_id').value = firstFilename; // 设置隐藏字段的值
            // checkAnnotationStatus(firstFilename, pageNum);
        } else {
            console.error(data.message);
        }
    }).catch(error => console.error('Error:', error));
});

function processPdf(filename) {
    fetch('/process_pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ filename: filename }),
    }).then(response => response.json()).then(data => {
        if (data.status === 'success') {
            console.log(data.result);
            // 清空前端的所有内容
            clearContentContainers();
            // 清空标注按钮的状态
            clearAnnotationButtons();
            // 显示自定义通知
            showNotification('PDF processed successfully and content cleared!');
            // // 检查并更新标注状态
            // checkAnnotationStatus(filename, pageNum);
            document.getElementById('item_id').value = filename;
        } else {
            console.error(data.message);
        }
    }).catch(error => console.error('Error:', error));
}


function showNotification(message) {
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notification-message');
    notificationMessage.textContent = message;

    // 创建关闭按钮并添加到通知中
    const closeButton = document.createElement('button');
    closeButton.textContent = 'Close';
    closeButton.addEventListener('click', closeNotification);
    notification.appendChild(closeButton);

    notification.style.display = 'block';
}

function closeNotification() {
    const notification = document.getElementById('notification');
    notification.style.display = 'none';
    // 移除关闭按钮，以便下次重新创建
    const closeButton = notification.querySelector('button');
    if (closeButton) {
        notification.removeChild(closeButton);
    }
}

function createAndSaveLabelsBulk(pdfDoc) {
    const filename = document.getElementById('item_id').value;
    const labels = [];

    for (let i = 1; i <= pdfDoc.numPages; i++) {
        const labelData = {
            filename: filename,
            page_number: i
        };
        for (const [key, value] of Object.entries(labelMapping)) {
            labelData[key] = false;
        }
        labels.push(labelData);
    }

    fetch('/save_labels_bulk', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ labels: labels })
    }).then(response => response.json()).then(data => {
        if (data.status !== 'success') {
            console.error(`Failed to save labels: ${data.message}`);
        }
    }).catch(error => console.error('Error:', error));
}




// 初始加载时检查按钮状态
function checkAnnotationStatus(filename, pageNumber) {
    fetch('/get_annotation_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ item_id: filename, page_number: pageNumber })
    }).then(response => response.json()).then(data => {
        if (data.status === 'success') {
            const labelsStatus = data.labels;
            annotationButtons.forEach(button => {
                const label = button.dataset.label;
                if (labelsStatus[label]) {
                    button.classList.add('annotated');
                } else {
                    button.classList.remove('annotated');
                }
            });
        } else {
            console.error(`Failed to get annotation status: ${data.message}`);
        }
    }).catch(error => console.error('Error:', error));
}

//实现pdf的切换功能
document.getElementById('prevBtn').addEventListener('click', function() {
    fetch('/prev_pdf').then(response => response.json()).then(data => {
        if (data.status === 'success') {
            const filename = data.filename;
            processPdf(filename);
            document.getElementById('item_id').value = filename; // 更新隐藏字段的值
        } else {
            console.error(data.message);
        }
    });
});

document.getElementById('nextBtn').addEventListener('click', function() {
    fetch('/next_pdf').then(response => response.json()).then(data => {
        if (data.status === 'success') {
            const filename = data.filename;
            processPdf(filename);
            document.getElementById('item_id').value = filename; // 更新隐藏字段的值
        } else {
            console.error(data.message);
        }
    });
});

// 清空标注按钮的状态
function clearAnnotationButtons() {
    annotationButtons.forEach(button => {
        button.classList.remove('annotated');
    });
}

// 保存主页状态
function saveHomePageState() {
    const state = {
        folderPath: document.getElementById('folderPath').value,
        pdfData: {
            filename: document.getElementById('item_id').value,
            pageNum: pageNum,
            displayType: currentDisplayType
        }
    };
    localStorage.setItem('homePageState', JSON.stringify(state));
    localStorage.setItem('fromLabelStats', 'true');  // 标记从标签统计页面返回
}

// 恢复主页状态
function restoreHomePageState() {
    const fromLabelStats = localStorage.getItem('fromLabelStats');
    if (fromLabelStats === 'true') {
        const savedState = localStorage.getItem('homePageState');
        if (savedState) {
            const state = JSON.parse(savedState);
            document.getElementById('folderPath').value = state.folderPath;
            processPdf(state.pdfData.filename);
            document.getElementById('item_id').value = state.pdfData.filename;
            pageNum = state.pdfData.pageNum;
            currentDisplayType = state.pdfData.displayType;
            // renderPage(pageNum);
            // checkAnnotationStatus(state.pdfData.filename, pageNum);
        }
        localStorage.removeItem('fromLabelStats');  // 恢复状态后删除标记
    }
}

// 在页面加载时恢复状态
document.addEventListener('DOMContentLoaded', function() {
    restoreHomePageState();
});

document.getElementById('viewStatsBtn').addEventListener('click', function() {
    saveHomePageState();
    window.location.href = '/label_stats';
});



// 标注按钮事件绑定
const annotationButtons = document.querySelectorAll('.annotation-btn');
annotationButtons.forEach(button => {
    button.addEventListener('click', function() {
        const label = this.dataset.label;
        const itemId = document.getElementById('item_id').value;
        const pageNumber = pageNum;
        console.log(`Sending label: ${label}, itemId: ${itemId}, pageNumber: ${pageNumber}`); // 调试信息
        updateLabel(label, itemId, pageNumber, this);
    });
});

//pdf翻页功能
document.getElementById('prev').addEventListener('click', function() {
    if (pageNum <= 1) {
        return;
    }
    pageNum--;
    renderPage(pageNum);
    clearAnnotationButtons()
    checkAnnotationStatus(document.getElementById('item_id').value, pageNum);
});

document.getElementById('next').addEventListener('click', function() {
    if (pageNum >= pdfDoc.numPages) {
        return;
    }
    pageNum++;
    renderPage(pageNum);
    clearAnnotationButtons()
    checkAnnotationStatus(document.getElementById('item_id').value, pageNum);
});










// 从指定路径读取并显示表格内容pdf
document.getElementById('tables_body').addEventListener('click', function() {
    const jsonFilePath = 'docs/show_tables_info/tables_body.json';

    loadDocument('/static/docs/show_tables_info/tables_body.pdf');
    currentDisplayType = DISPLAY_TYPES.TABLES;


    fetch(`/load-json-data/?path=${encodeURIComponent(jsonFilePath)}`)
        .then(response => response.json())
        .then(data => {
            if (currentDisplayType === DISPLAY_TYPES.TABLES) {
                currentImageData = data;
                displayImagesForPage(pageNum, data, 'table_body_bbox');
            }
        })
        .catch(error => console.error('Error loading table images:', error));
});



//指定路径读取并显示表格标题pdf
document.getElementById('tables_caption').addEventListener('click', function() {
    loadDocument('/static/docs/show_tables_info/tables_caption.pdf');
        // 设置当前显示类型为 NONE
    currentDisplayType = DISPLAY_TYPES.NONE;
    // 清空可能包含先前内容的容器
    clearContentContainers();
});



//指定路径读取并显示图片标题pdf
document.getElementById('images_caption').addEventListener('click', function() {
    loadDocument('/static/docs/show_images_info/images_caption.pdf');
        // 设置当前显示类型为 NONE
    currentDisplayType = DISPLAY_TYPES.NONE;
    // 清空可能包含先前内容的容器
    clearContentContainers();
});



//指定路径读取并显示丢弃块pdf
document.getElementById('discarded_blocks').addEventListener('click', function() {
    loadDocument('/static/docs/show_discarded_info/discarded.pdf');
        // 设置当前显示类型为 NONE
    currentDisplayType = DISPLAY_TYPES.NONE;
    // 清空可能包含先前内容的容器
    clearContentContainers();
});




//指定路径读取并显示段落排序pdf
document.getElementById('para_sort').addEventListener('click', function() {
    loadDocument('/static/docs/show_para_info/para_sort.pdf');
        // 设置当前显示类型为 NONE
    currentDisplayType = DISPLAY_TYPES.NONE;
    // 清空可能包含先前内容的容器
    clearContentContainers();
});



//指定路径读取并显示标题pdf
document.getElementById('title').addEventListener('click', function() {
    loadDocument('/static/docs/show_para_info/title.pdf');
        // 设置当前显示类型为 NONE
    currentDisplayType = DISPLAY_TYPES.NONE;
    // 清空可能包含先前内容的容器
    clearContentContainers();
});



//指定路径读取并显示文本pdf
document.getElementById('extract_text').addEventListener('click', function() {
    const jsonFilePath = 'docs/show_para_info/text.json';  // JSON 文件的路径

    // 假设您已经定义了加载文档的函数
    loadDocument('/static/docs/show_para_info/text.pdf');

    currentDisplayType = DISPLAY_TYPES.TEXT;

       fetch(`/load-json-data/?path=${encodeURIComponent(jsonFilePath)}`)
        .then(response => response.json())
        .then(data => {
            if (currentDisplayType === DISPLAY_TYPES.TEXT) {
                currentTextData = data;  // 存储数据以便在翻页时使用
                displayTextContentForPage(pageNum, data, 'text_bbox');
            }
        })
        .catch(error => console.error('Error loading text data:', error));
});


//指定路径读取并显示图片内容pdf
document.getElementById('images_body').addEventListener('click', function() {
  
    const jsonFilePath = 'docs/show_images_info/images_body.json';  

    currentDisplayType = DISPLAY_TYPES.IMAGES;

    // 按钮点击时获取指定的JSON文件路径
    loadDocument('/static/docs/show_images_info/images_body.pdf');

    fetch(`/load-json-data/?path=${encodeURIComponent(jsonFilePath)}`)
        .then(response => response.json())
        .then(data => {
             // 存储数据以便在翻页时使用
            if (currentDisplayType === DISPLAY_TYPES.IMAGES) {
                currentImageData = data;
                displayImagesForPage(pageNum, data,'image_body_bbox');
            }
        })
        .catch(error => console.error('Error loading images:', error));

});





//从指定路径读取json文件并显示行间公式
document.getElementById('extract-interline_equations').addEventListener('click', function() {
    const jsonFilePath = 'docs/show_equation_info/interline_equations.json';
    
    currentDisplayType = DISPLAY_TYPES.INTERLINE_FORMULAS;

    // 加载PDF文档
    loadDocument('/static/docs/show_equation_info/interline_equations.pdf');

    fetch(`/load-json-data/?path=${encodeURIComponent(jsonFilePath)}`)
        .then(response => response.json())
        .then(data => {

             // 存储数据以便在翻页时使用
             if (currentDisplayType === DISPLAY_TYPES.INTERLINE_FORMULAS) {
                currentFormulaData = data; 
                displayFormulasForPage(pageNum, data,'interline_equations');
            }
        })
        .catch(error => console.error('Error loading formulas:', error));
});


//从指定路径读取json文件并显示行内公式
document.getElementById('extract-inline_equations').addEventListener('click', function() {
    const jsonFilePath = 'docs/show_equation_info/inline_equations.json'; // 确保路径正确
    
    currentDisplayType = DISPLAY_TYPES.INLINE_FORMULAS;

    // 加载PDF文档
    loadDocument('/static/docs/show_equation_info/inline_equations.pdf');

    fetch(`/load-json-data/?path=${encodeURIComponent(jsonFilePath)}`)
        .then(response => response.json())
        .then(data => {
            
             // 存储数据以便在翻页时使用
             if (currentDisplayType === DISPLAY_TYPES.INLINE_FORMULAS) {
                console.log("Loaded data for inline formulas:", data);
                currentFormulaData = data; 
                displayFormulasForPage(pageNum, data, 'inline_equations');
            }  // 指定行内公式
        })
        .catch(error => console.error('Error loading inline formulas:', error));
});


document.getElementById('exportBtn').addEventListener('click', function() {
    fetch('/export_json').then(response => {
        if (response.ok) {
            return response.blob();
        }
        return response.json().then(data => {
            throw new Error(data.message);
        });
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'page_data.json';
        a.click();
        URL.revokeObjectURL(url);
    }).catch(error => {
        console.error('Error:', error.message);
    });
});


function updateLabel(label, itemId, pageNumber, button) {
    console.log(`Updating label with: label=${label}, itemId=${itemId}, pageNumber=${pageNumber}`);
    
    fetch('/annotate_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            item_id: itemId,
            page_number: pageNumber,
            label: encodeURIComponent(label)  // 对标签进行URL编码
        })
    }).then(response => {
        if (!response.ok) {
            return response.text().then(text => { throw new Error(text) });
        }
        return response.json();
    }).then(data => {
        if (data.status === 'success') {
            console.log(`Annotation ${data.action}: ${data.message}`);

            // 更新按钮状态
            if (data.action === 'added') {
                button.classList.add('annotated');
            } else {
                button.classList.remove('annotated');
            }

            // 显示成功消息
            document.getElementById('success-message').style.display = 'block';
            setTimeout(() => {
                document.getElementById('success-message').style.display = 'none';
            }, 2000); // 显示2秒后隐藏
        } else {
            console.error(`Annotation failed: ${data.message}`);
        }
    }).catch(error => console.error('Error:', error));
}

//通过pdf.js实现pdf的翻页功能

function renderPage(num) {
    pageRendering = true;
    pdfDoc.getPage(num).then(function(page) {
        var viewport = page.getViewport({scale: scale});
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        var renderContext = {
            canvasContext: ctx,
            viewport: viewport
        };
        var renderTask = page.render(renderContext);
        renderTask.promise.then(function() {
            pageRendering = false;
            if (pageNumPending !== null) {
                renderPage(pageNumPending);
                pageNumPending = null;
            }
            document.getElementById('page_num').textContent = num;
        // 根据当前显示类型决定如何展示内容
        switch (currentDisplayType) {
            case DISPLAY_TYPES.IMAGES:
            case DISPLAY_TYPES.TABLES:
                if (currentImageData) {
                    displayImagesForPage(num, currentImageData, currentDisplayType);
                }
                break;
            case DISPLAY_TYPES.INLINE_FORMULAS:
            case DISPLAY_TYPES.INTERLINE_FORMULAS:
                if (currentFormulaData) {
                    displayFormulasForPage(num, currentFormulaData, currentDisplayType);
                }
                break;

            case DISPLAY_TYPES.TEXT:
                if (currentTextData) {
                    displayTextContentForPage(num, currentTextData,currentDisplayType);
                }
                break;
            }
        });
    });
}

// 加载PDF文档并获取总页数
function loadDocument(pdfUrl) {
    const timestamp = new Date().getTime(); // 获取当前时间的时间戳
    const urlWithTimestamp = `${pdfUrl}?t=${timestamp}`; // 添加时间戳到URL

    pdfjsLib.getDocument(urlWithTimestamp).promise.then(function(newPdfDoc) {
        pdfDoc = newPdfDoc;
        document.getElementById('page_count').textContent = pdfDoc.numPages;
        pageNum = 1; // 从第一页开始显示新文档
        renderPage(pageNum);

        // 创建所有页面的标签数据并批量发送到后端保存
        createAndSaveLabelsBulk(pdfDoc);
        checkAnnotationStatus(document.getElementById('item_id').value, pageNum)
    }).catch(function(error) {
        console.error('Error loading the PDF document: ', error);
    });
}



// 清空图片和公式容器
function clearContentContainers() {
    const imageContainer = document.getElementById('image-container');
    const formulasContainer = document.getElementById('formulas-container');
    const textContainer = document.getElementById('text-container');

    if (imageContainer) {
        imageContainer.innerHTML = '';  // 清空图片容器
    }
    if (formulasContainer) {
        formulasContainer.innerHTML = '';  // 清空公式容器
    }
    if (textContainer) {
        textContainer.innerHTML = '';  // 清空图片容器
    }
}


// 实现跟随pdf的翻页图片内容随之变化的功能
function displayImagesForPage(num, data, bboxType) {
    const pageKey = `page_idx_${num - 1}`; // 调整索引，确保从0开始
    const items = data[pageKey];
    if (!items) {
        console.error(`No items found for: ${pageKey}`);
        return;  // 如果没有找到数据，提前返回避免错误
    }

    clearContentContainers()
    const imageContainer = document.getElementById('image-container');

    for (const itemKey in items) {
        const itemInfo = items[itemKey];
        const itemElement = document.createElement('img');
        itemElement.src = `/static/images/${itemInfo.image_path}`; // 确保路径正确
        itemElement.setAttribute('alt', 'Page Image');
        imageContainer.appendChild(itemElement);
        itemElement.dataset.bbox = itemInfo[bboxType].join(','); // 使用动态bbox类型
    }
}


// 实现跟随pdf的翻页公式内容随之变化的功能
function displayFormulasForPage(num, data, formulaType) {
    const pageKey = `page_idx_${num - 1}`;
    const formulasContainer = document.getElementById('formulas-container');
    clearContentContainers();

    if (formulaType === 'inline_equations') {
        const bboxArray = data[pageKey]?.inline_equations_bbox;
        const formulasArray = data[pageKey]?.inline_equations;

        if (!formulasArray || !bboxArray) {
            console.error(`No inline formulas found for: ${pageKey}`);
            return;
        }

        formulasArray.forEach((formula, index) => {
            const bbox = bboxArray[index];
            const formulaElement = document.createElement('div');
            formulaElement.textContent = `Formula: ${formula}`;
            katex.render(formula, formulaElement, {
                throwOnError: false,
                strict: function(errorCode, errorMsg, token) {
                    if (errorCode === 'mathVsTextAccents') {
                        return 'ignore';
                    }
                    return 'warn';
                }
            });
            formulasContainer.appendChild(formulaElement);
        });
    } else if (formulaType === 'interline_equations') {
        const formulas = data[pageKey];

        if (!formulas) {
            console.error('No interline formulas found for: ', pageKey);
            return;
        }

        Object.entries(formulas).forEach(([key, item]) => {
            const bbox = item['interline_equations_bbox'];
            const content = item['interline_equations_content'];
            const formulaElement = document.createElement('div');
            formulaElement.textContent = `Formula: ${content}`;
            katex.render(content, formulaElement, {
                throwOnError: false,
                strict: function(errorCode, errorMsg, token) {
                    if (errorCode === 'mathVsTextAccents') {
                        return 'ignore';
                    }
                    return 'warn';
                }
            });
            formulasContainer.appendChild(formulaElement);
        });
    }
}



function displayTextContentForPage(num, data, bboxType) {
    const pageKey = `page_idx_${num - 1}`; // 调整索引，确保从0开始
    const texts = data[pageKey];
    console.log('Text data:', texts); // 调试输出查看文本数据

    if (!texts) {
        console.error(`No text content found for: ${pageKey}`);
        return;  // 如果没有找到数据，提前返回避免错误
    }

    clearContentContainers();
    const textContainer = document.getElementById('text-container');
    if (!textContainer) {
        console.error('Text container not found'); // 检查容器是否被正确获取
        return;
    }

    Object.keys(texts).forEach(textKey => {
        const textInfo = texts[textKey];
        if (textInfo && textInfo[bboxType]) { // 确保存在文本信息和对应的bbox
            const textElement = document.createElement('div');
            textElement.textContent = textInfo['text_content']; // 确保使用正确的键名获取文本内容
            textElement.className = 'text-content'; // 可以通过CSS来控制样式
            textContainer.appendChild(textElement);
            textElement.dataset.bbox = textInfo[bboxType].join(','); // 使用动态bbox类型
            console.log('Added text:', textInfo['text_content']); // 输出被添加的文本信息
        } else {
            console.error(`Missing text content or bbox for key: ${textKey}`);
        }
    });
}




