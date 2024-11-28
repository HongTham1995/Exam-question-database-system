import re
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from bs4 import BeautifulSoup
from datetime import datetime
import pyodbc
import requests


app = Flask(__name__)
app.secret_key = "your_secret_key"
def connect_db_web():
    try:
        conn = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=127.0.0.1;'    
            'DATABASE=DLTT;'      
            'UID=sa;'               
            'PWD=123456;'           
        )
        print("Kết nối tới SQL Server thành công.")
        return conn
    except pyodbc.Error as e:
        print("Lỗi kết nối tới SQL Server:", e)
        return None

# Trang chủ: hiển thị tất cả câu hỏi
@app.route('/app_web')
def index_web():
    connection = connect_db_web()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu", "danger")
        return render_template('index_web.html', questions=[])

    cursor = connection.cursor()
    try:
        # Sử dụng JOIN để lấy thông tin từ cả hai bảng Cau_hoi và Mota
        cursor.execute("""
            SELECT 
                ch.ID, 
                ch.cau_hoi, 
                ch.dap_an_a, 
                ch.dap_an_b, 
                ch.dap_an_c, 
                ch.dap_an_d, 
                ch.dap_an_dung, 
                m.De_tai, 
                m.Nguon, 
                m.Link, 
                m.Thoigian,  -- Corrected query
                ch.Nguoi_kiem_duyet
                
            FROM 
                Cau_hoi AS ch
            JOIN 
                Mota AS m 
            ON 
                ch.maMT = m.maMT
        """)
        questions = cursor.fetchall()
    except Exception as e:
        flash(f"Lỗi khi truy vấn cơ sở dữ liệu: {e}", "danger")
        questions = []
    finally:
        cursor.close()
        connection.close()

    
    return render_template('index_web.html', questions=questions)



# Xóa câu hỏi
@app.route('/app_web/web_delete_question/<id>')
def web_delete_question(id):
    connection = connect_db_web()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu", "danger")
        return redirect(url_for('index_web'))

    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM Cau_hoi WHERE ID = ?", (id,))
        connection.commit()
        flash("Xóa câu hỏi thành công", "success")
    except Exception as e:
        flash(f"Lỗi khi xóa câu hỏi: {e}", "danger")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('index_web'))


# Sửa câu hỏi
# Sửa câu hỏi
@app.route('/web_edit_question/<id>', methods=['GET', 'POST'])
def web_edit_question(id):
    connection = connect_db_web()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu", "danger")
        return redirect(url_for('index_web'))

    cursor = connection.cursor()
    if request.method == 'POST':
        # Collect form data excluding Thoigian, De_tai, Nguon, and Link
        question_data = {
            'cau_hoi': request.form['cau_hoi'],
            'dap_an_a': request.form['dap_an_a'],
            'dap_an_b': request.form['dap_an_b'],
            'dap_an_c': request.form['dap_an_c'],
            'dap_an_d': request.form['dap_an_d'],
            'dap_an_dung': request.form['dap_an_dung'],
            'nguoi_kiem_duyet': request.form['nguoi_kiem_duyet']
             # Sử dụng đúng tên khóa
        }

        # Ensure no fields are left empty
        if not all(question_data.values()):
            flash("Tất cả các trường đều phải được điền!", "warning")
            return redirect(url_for('web_edit_question', id=id))

        try:
            # Update query for all fields excluding Thoigian, De_tai, Nguon, and Link
            query = """
                UPDATE Cau_hoi
                SET cau_hoi = ?, 
                    dap_an_a = ?, 
                    dap_an_b = ?, 
                    dap_an_c = ?, 
                    dap_an_d = ?, 
                    dap_an_dung = ?, 
                    nguoi_kiem_duyet = ?
                   
                WHERE ID = ?
            """
            values = (*question_data.values(), id)
            cursor.execute(query, values)
            connection.commit()
            flash("Cập nhật câu hỏi thành công", "success")
        except Exception as e:
            flash(f"Lỗi khi sửa câu hỏi: {e}", "danger")
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('index_web'))

    # Lấy câu hỏi để sửa (khi truy cập GET)
    try:
        cursor.execute("SELECT * FROM Cau_hoi WHERE ID = ?", (id,))
        question = cursor.fetchone()
        if not question:
            flash("Câu hỏi không tồn tại", "warning")
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"Lỗi khi truy vấn câu hỏi: {e}", "danger")
        question = None
    finally:
        cursor.close()
        connection.close()

    return render_template('web_edit_question.html', question=question)



# TÌM
@app.route('/web_search_questions', methods=['GET'])
def web_search_questions():
    source = request.args.get('source', '')
    topic = request.args.get('topic', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    data_type = request.args.get('data_type', '')  # Lấy thêm data_type từ request
    
    # Xử lý và định dạng ngày tháng
    if start_date:
        start_date = start_date.replace('T', ' ') + ":00.000"
    if end_date:
        end_date = end_date.replace('T', ' ') + ":59.999"

    connection = connect_db_web()

    if connection is None:
        return jsonify({"success": False, "message": "Lỗi kết nối cơ sở dữ liệu"})

    cursor = connection.cursor()

    try:
        # Xây dựng câu truy vấn SQL
        query_sql = """
            SELECT 
                ch.ID, 
                ch.cau_hoi, 
                ch.dap_an_a, 
                ch.dap_an_b, 
                ch.dap_an_c, 
                ch.dap_an_d, 
                ch.dap_an_dung, 
                m.De_tai, 
                m.Nguon, 
                m.Thoigian,
                ch.Nguoi_kiem_duyet  -- Check this field
                
            FROM 
                Cau_hoi AS ch
            JOIN 
                Mota AS m 
            ON 
                ch.maMT = m.maMT

            WHERE 
        """
        conditions = []
        params = []

        
        if source:
            conditions.append("m.Nguon LIKE ?")
            params.append(f"%{source}%")
        if topic != "all":
            conditions.append("m.De_tai LIKE ?")
            params.append(f"%{topic}%")
        if start_date:
            conditions.append("m.Thoigian >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("m.Thoigian <= ?")
            params.append(end_date)

        if data_type == "revised":
            conditions.append("ch.Nguoi_kiem_duyet IS NOT NULL")
        elif data_type == "unrevised":
            conditions.append("ch.Nguoi_kiem_duyet IS NULL")

        if not conditions:
            conditions.append("1=1")

        query_sql += " AND ".join(conditions)
        
        cursor.execute(query_sql, params)

        # Lấy dữ liệu và chuyển thành danh sách các câu hỏi
        rows = cursor.fetchall()
        questions = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
       
        return jsonify({"success": True, "questions": questions})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

    finally:
        cursor.close()
        connection.close()



def get_text_or_none(element):
    """Trả về text của element nếu tồn tại, ngược lại trả về None."""
    return element.get_text(strip=True) if element else None

def fetch_data(url):
    # Gửi yêu cầu GET đến trang
    response = requests.get(url)
    response.raise_for_status()  # Kiểm tra lỗi nếu có

    # Phân tích HTML bằng BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Lấy phần tử <div class="col-md-7 middle-col">
    middle_col = soup.find('div', class_='col-md-7 middle-col')
    if not middle_col:
        print("Không tìm thấy div col-md-7 middle-col.")
        return []

    # Lấy thông tin tiêu đề từ <div class="vj-more">
    vj_more = middle_col.find('div', class_='vj-more')
    if vj_more:
        a_tag = vj_more.find('a')
        if a_tag:
            title = a_tag.get_text(strip=True).split("12")[1].strip()  # Lấy phần sau số 12
        else:
            title = "Tiêu đề không tìm thấy"
    else:
        title = "Tiêu đề không tìm thấy"
    
    print(f"Tiêu đề bài học: {title}")

    # Danh sách chứa các câu hỏi và đáp án
    questions = []

    # Duyệt qua các câu hỏi và đáp án
    question_tags = middle_col.find_all('p')
    i = 0  # Chỉ số để duyệt qua các thẻ <p>

    while i < len(question_tags):
        question_tag = question_tags[i]
        
        # Kiểm tra nếu thẻ <p> chứa câu hỏi
        if question_tag.b and 'Câu' in question_tag.b.get_text():
            # Lấy nội dung câu hỏi và loại bỏ phần trước dấu ":"
            full_question_text = question_tag.get_text(strip=True).split(":", 1)[1].strip()

            # Tìm vị trí dấu "?" hoặc ":" và cắt chuỗi từ đầu đến dấu đó
            question_end_index = min(full_question_text.find('?'), full_question_text.find(':'))
            if question_end_index != -1:
                question_text = full_question_text[:question_end_index + 1].strip()  # Lấy đến và bao gồm dấu "?" hoặc ":"
            else:
                question_text = full_question_text

            # Kiểm tra nếu câu hỏi kết thúc bằng dấu "?" và có đủ điều kiện
            if question_text.endswith('?') and 'Trả lời:' not in question_text:
                # Tìm đáp án từ các thẻ <p> tiếp theo
                answers = []
                i += 1  # Tiến đến các thẻ <p> tiếp theo
                for _ in range(4):  # Chỉ lấy 4 đáp án A, B, C, D
                    if i < len(question_tags):
                        answer_text = question_tags[i].get_text(strip=True)
                        # Loại bỏ phần "A.", "B.", "C.", "D." nếu có
                        answer_text = answer_text.replace("A.", "").replace("B.", "").replace("C.", "").replace("D.", "").strip()
                        # Kiểm tra xem đáp án có hợp lệ không (không trống và không phải "Đáp án:")
                        if answer_text and "Đáp án" not in answer_text:
                            answers.append(answer_text)
                        i += 1  # Tiến đến thẻ <p> tiếp theo

                # Kiểm tra nếu có đủ 4 đáp án hợp lệ
                if len(answers) == 4:
                    # Lấy đáp án đúng từ phần <section class="toggle-content">
                    dap_an_dung = None
                    section_tag = middle_col.find_next('section', class_='toggle')
                    if section_tag:
                        toggle_content = section_tag.find('div', class_='toggle-content')
                        if toggle_content:
                            # Tìm đáp án đúng trong phần "Đáp án:"
                            toggle_text = toggle_content.get_text(strip=True)
                            if 'Đáp án:' in toggle_text:
                                dap_an_dung = toggle_text.split('Đáp án:')[1].split('Giải thích:')[0].strip()

                    # Nếu có câu hỏi và đáp án đúng, lưu vào danh sách
                    if dap_an_dung:
                        # Xử lý bỏ dấu chấm không cần thiết trong đáp án đúng
                        dap_an_dung = dap_an_dung.strip().replace(".", "") if dap_an_dung else None

                        questions.append({
                            'question': question_text,
                            'answers': answers,
                            'correct_answer': dap_an_dung
                        })
        i += 1  # Tiến đến thẻ <p> tiếp theo

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_questions = [
        (
            q['question'],       # Câu hỏi
            q['answers'][0],     # Đáp án A
            q['answers'][1],     # Đáp án B
            q['answers'][2],     # Đáp án C
            q['answers'][3],     # Đáp án D
            q['correct_answer']  # Đáp án đúng
        )
        for q in questions
    ]
    
    # Trả về kết quả dưới dạng danh sách các câu hỏi
    return formatted_questions, title, current_time


def extract_question_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Lỗi khi kết nối tới URL:", e)
        return [], None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Lấy tiêu đề bài viết
    title_tag = soup.find('h1', class_='the-article-title')
    title_text = title_tag.get_text(strip=True).split(":")[-1].strip() if title_tag else "Tiêu đề không tìm thấy"

    # Lấy thời gian hiện tại
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Tìm tất cả các phần tử câu hỏi
    questions_data = []
    questions = soup.find_all('form', class_='box-van-dap form-cauhoi')

    for question in questions:
        question_number = question.find('span', class_='ptitle').get_text(strip=True)
        question_text = question.find('span', class_='underline').get_text(strip=True)
        
        # Lấy các đáp án và loại bỏ ký tự A., B., C., D.
        answers = []
        for label in question.find_all('label', class_='label-radio'):
            answer_text = label.get_text(strip=True)
            # Loại bỏ ký tự "A.", "B.", "C.", "D." nếu có
            if answer_text[1] == '.':
                answer_text = answer_text[2:].strip()  # Bỏ ký tự đầu tiên và dấu chấm
            answers.append(answer_text)

        # Đảm bảo có đúng 4 đáp án (A, B, C, D)
        while len(answers) < 4:
            answers.append(None)

        # Thêm dữ liệu câu hỏi (chưa có đáp án đúng)
        questions_data.append({
            'question_number': question_number,
            'question_text': question_text,
            'answers': answers,
            'correct_answer': None  # Sẽ được thêm sau
        })

    # Tìm phần đáp án từ bảng
    answer_section = soup.find('table', class_='table text-center')
    sorted_answers = []

    if answer_section:
        tbody = answer_section.find('tbody')
        if tbody:
            ans_text = tbody.get_text(strip=True)
            pattern = r"Câu (\d+)\s*([A-D])"
            matches = re.findall(pattern, ans_text)
            
            # Sắp xếp câu hỏi theo thứ tự và trích xuất đáp án
            answers = [(int(match[0]), match[1]) for match in matches]
            answers.sort(key=lambda x: x[0])
            sorted_answers = [answer[1] for answer in answers]
        else:
            print("Không tìm thấy tbody trong answer_section.")
    else:
        print("Không tìm thấy phần đáp án.")
    
    # Thêm từng đáp án từ sorted_answers vào đối tượng tương ứng trong questions_data
    for i in range(len(questions_data)):
        if i < len(sorted_answers):
            questions_data[i]['correct_answer'] = sorted_answers[i]

    # Chuyển đổi questions_data thành định dạng tương thích với process_questions
    formatted_questions = [
        (
            q['question_text'],       # Câu hỏi
            q['answers'][0],          # Đáp án A
            q['answers'][1],          # Đáp án B
            q['answers'][2],          # Đáp án C
            q['answers'][3],          # Đáp án D
            q['correct_answer']       # Đáp án đúng
        )
        for q in questions_data
    ]

    return formatted_questions, title_text, current_time
       


def insert_data(connection, questions, title, nguon, url, timestamp):
    """
    Hàm để chèn dữ liệu vào bảng Cau_hoi và Mota trong cơ sở dữ liệu với kiểm tra dữ liệu trùng.
    """

    # Kiểm tra nếu không có câu hỏi để chèn
    if not questions:
        print("Không có dữ liệu để chèn vào database.")
        return

    try:
        cursor = connection.cursor()

        # Chuyển đổi thời gian sang định dạng chuẩn SQL Server
        try:
            thoi_gian = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            formatted_timestamp = thoi_gian.strftime('%Y-%m-%d %H:%M:%S.000')
        except ValueError as e:
            print(f"Lỗi chuyển đổi thời gian: {e}")
            raise Exception("Thời gian không đúng định dạng.")

        # Kiểm tra nếu metadata đã tồn tại trong bảng Mota
        check_sql = """
        SELECT MaMT FROM Mota 
        WHERE De_tai = ? AND Nguon = ? AND Thoigian = ?
        """
        cursor.execute(check_sql, (title, nguon, formatted_timestamp))
        result = cursor.fetchone()

        if result:
            maMT = result[0]
            print(f"Metadata đã tồn tại với maMT: {maMT}")
        else:
            # Tạo mã MaMT mới nếu chưa tồn tại
            # Tính toán mã MaMT mới theo định dạng MTTT_1, MTTT_2,...
            # Lấy mã maMT lớn nhất trong bảng Mota
            select_sql_maMT = "SELECT MAX(CAST(SUBSTRING(MaMT, 6, LEN(MaMT)) AS INT)) FROM Mota WHERE MaMT LIKE 'MTTT_%'"
            cursor.execute(select_sql_maMT)
            max_maMT_result = cursor.fetchone()

            # Tính toán MaMT mới
            if max_maMT_result[0] is not None:
                new_maMT = f"MTTT_{max_maMT_result[0] + 1}"
            else:
                new_maMT = "MTTT_1"  # Nếu bảng chưa có bản ghi nào

            # Thêm metadata vào bảng Mota với maMT tính toán
            insert_sql_dltt = """
            INSERT INTO Mota (MaMT, De_tai, Nguon, Link, Thoigian) 
            VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insert_sql_dltt, (new_maMT, title, nguon, url, formatted_timestamp))
            connection.commit()  # Commit giao dịch để đảm bảo dữ liệu được lưu

            print(f"Đã tạo metadata mới với maMT: {new_maMT}")

        # Duyệt qua từng câu hỏi để chèn vào bảng Cau_hoi
        insert_sql_cau_hoi = """
        INSERT INTO Cau_hoi (ID, cau_hoi, dap_an_a, dap_an_b, dap_an_c, dap_an_d, dap_an_dung, Nguoi_kiem_duyet, maMT) 
        VALUES (?, ?, ?, ?, ?, ?, ?, null, ?)
        """

        inserted_count = 0
        for question in questions:
            try:
                cau_hoi, dap_an_a, dap_an_b, dap_an_c, dap_an_d, dap_an_dung = question

                # Kiểm tra các trường hợp null hoặc dữ liệu không hợp lệ
                if None in [cau_hoi, dap_an_a, dap_an_b, dap_an_c, dap_an_d, dap_an_dung]:
                    print(f"Câu hỏi không hợp lệ và bị bỏ qua: {question}")
                    continue

                # Lấy ID của câu hỏi, tính toán theo định dạng TT_1, TT_2, ...
                select_sql_id = "SELECT COUNT(*) FROM Cau_hoi"
                cursor.execute(select_sql_id)
                count_result = cursor.fetchone()

                if count_result and count_result[0] is not None:
                    new_id = f"TT_{count_result[0] + 1}"
                else:
                    new_id = "TT_1"  # Nếu bảng chưa có bản ghi nào

                
                print(f"Đã tạo ID mới với ID: {new_id}")

                # Chèn câu hỏi vào bảng Cau_hoi
                cursor.execute(insert_sql_cau_hoi, (new_id, cau_hoi, dap_an_a, dap_an_b, dap_an_c, dap_an_d, dap_an_dung, new_maMT))
                inserted_count += 1
                print(f"Đã chèn câu hỏi: {cau_hoi}")

            except Exception as e:
                print(f"Lỗi khi chèn câu hỏi {question[0]}: {e}")

        # Commit tất cả thay đổi nếu có ít nhất một câu hỏi được chèn
        if inserted_count > 0:
            connection.commit()
            print(f"Đã chèn {inserted_count}/{len(questions)} câu hỏi vào bảng Cau_hoi.")
        else:
            print("Không có câu hỏi nào được chèn vào database.")

    except Exception as e:
        print(f"Lỗi trong quá trình xử lý: {e}")
        connection.rollback()  # Rollback nếu xảy ra lỗi
    finally:
        if cursor:
            cursor.close()
        connection.close()






# Chỉ định duy nhất một endpoint '/fetch_questions'
@app.route('/fetch_questions', methods=['POST'])
def fetch_questions():
    try:
        data = request.get_json()  # Lấy dữ liệu JSON từ frontend
        #print(f"Received data: {data}")  # In dữ liệu ra console để kiểm tra
        url = data.get('url')  # Lấy URL từ dữ liệu

        if not url:
            raise ValueError("URL is missing in the request")

        # Gọi hàm extract_question_data(url)
        if "doctailieu" in url:
            questions, title, timestamp = extract_question_data(url)
            connection = connect_db_web()
            insert_data(connection, questions, title, "Doctailieu", url, timestamp)
        elif "vietjack" in url:
            questions, title, timestamp = fetch_data(url)
            connection = connect_db_web()
            insert_data(connection, questions, title, "VietJack", url, timestamp)
        else:
            # Nếu không có từ nào trong URL, có thể xử lý tình huống này (ví dụ: mặc định hoặc thông báo lỗi)
            questions, title, timestamp = None, None, None

        #print(f"Extracted data: {questions}, {title}, {timestamp}")
        
        if questions:
            return jsonify({
                'success': True,
                'questions': questions,
                'title': title,
                'timestamp': timestamp
            })
        else:
            return jsonify({'success': False, 'message': 'Không thể lấy dữ liệu câu hỏi.'})
    
    except Exception as e:
        print(f"Lỗi khi xử lý yêu cầu: {e}")
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/app_web')
def app_web():
    return render_template('index_web.html')   


# Hàm kết nối với SQL Server
def connect_db_ai():
    try:
        conn = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=127.0.0.1;'    
            'DATABASE=DLTS;'      
            'UID=sa;'               
            'PWD=123456;'           
        )
        print("Kết nối tới SQL Server thành công.")
        return conn
    except pyodbc.Error as e:
        print("Lỗi kết nối tới SQL Server:", e)
        return None

# Trang chủ: hiển thị tất cả câu hỏi
@app.route('/app_ai')
def index_ai():
    connection = connect_db_ai()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu", "danger")
        return render_template('index_AI.html', questions=[])

    cursor = connection.cursor()
    try:
        # Sử dụng JOIN để lấy thông tin từ cả hai bảng Cau_hoi và Mota
        cursor.execute("""
            SELECT 
                ch.ID, 
                ch.cau_hoi, 
                ch.dap_an_a, 
                ch.dap_an_b, 
                ch.dap_an_c, 
                ch.dap_an_d, 
                ch.dap_an_dung, 
                m.De_tai, 
                m.Nguon, 
                m.Thoigian,
                ch.Nguoi_kiem_duyet_1,
                ch.Nguoi_kiem_duyet_2
            FROM 
                Cau_hoi AS ch
            JOIN 
                Mota AS m 
            ON 
                ch.maMT = m.maMT
        """)
        questions = cursor.fetchall()
    except Exception as e:
        flash(f"Lỗi khi truy vấn cơ sở dữ liệu: {e}", "danger")
        questions = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('index_AI.html', questions=questions)


# Xóa câu hỏi
@app.route('/app_ai/ai_delete_question/<id>')
def ai_delete_question(id):
    connection = connect_db_ai()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu", "danger")
        return redirect(url_for('index_ai'))

    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM Cau_hoi WHERE ID = ?", (id,))
        connection.commit()
        flash("Xóa câu hỏi thành công", "success")
    except Exception as e:
        flash(f"Lỗi khi xóa câu hỏi: {e}", "danger")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('index_ai'))




# Sửa câu hỏi
@app.route('/ai_edit_question/<id>', methods=['GET', 'POST'])
def ai_edit_question(id):
    connection = connect_db_ai()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu", "danger")
        return redirect(url_for('index_ai'))

    cursor = connection.cursor()
    if request.method == 'POST':
        question_data = {
            'cau_hoi': request.form['cau_hoi'],
            'dap_an_a': request.form['dap_an_a'],
            'dap_an_b': request.form['dap_an_b'],
            'dap_an_c': request.form['dap_an_c'],
            'dap_an_d': request.form['dap_an_d'],
            'dap_an_dung': request.form['dap_an_dung'],
            'Nguoi_kiem_duyet_1': request.form['Nguoi_kiem_duyet_1'],
            'Nguoi_kiem_duyet_2': request.form['Nguoi_kiem_duyet_2']
        }

        if not all(question_data.values()):
            flash("Tất cả các trường đều phải được điền!", "warning")
            return redirect(url_for('edit_question', id=id))

        try:
            query = """
                UPDATE Cau_hoi
                SET cau_hoi = ?, dap_an_a = ?, dap_an_b = ?, dap_an_c = ?, dap_an_d = ?, dap_an_dung = ?,Nguoi_kiem_duyet_1=?,Nguoi_kiem_duyet_2=?
                WHERE ID = ?
            """
            values = (*question_data.values(), id)
            cursor.execute(query, values)
            connection.commit()
            flash("Cập nhật câu hỏi thành công", "success")
        except Exception as e:
            flash(f"Lỗi khi sửa câu hỏi: {e}", "danger")
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('index_ai'))

    # Lấy câu hỏi để sửa (khi truy cập GET)
    try:
        cursor.execute("SELECT * FROM Cau_hoi WHERE ID = ?", (id,))
        question = cursor.fetchone()
        if not question:
            flash("Câu hỏi không tồn tại", "warning")
            return redirect(url_for('index_ai'))
    except Exception as e:
        flash(f"Lỗi khi truy vấn câu hỏi: {e}", "danger")
        question = None
    finally:
        cursor.close()
        connection.close()

    return render_template('edit_question.html', question=question)



# TÌM

# Tìm kiếm câu hỏi
@app.route('/ai_search_questions', methods=['GET'])
def ai_search_questions():
   
    source = request.args.get('source', '')
    topic = request.args.get('topic', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    data_type = request.args.get('data_type', '')
    print("datatype"+data_type)
    # Xử lý và định dạng ngày tháng
    if start_date:
        start_date = start_date.replace('T', ' ') + ":00.000"
    if end_date:
        end_date = end_date.replace('T', ' ') + ":59.999"

    connection = connect_db_ai()

    if connection is None:
        return jsonify({"success": False, "message": "Lỗi kết nối cơ sở dữ liệu"})

    cursor = connection.cursor()

    try:
        # Xây dựng câu truy vấn SQL
        query_sql = """
            SELECT 
                ch.ID, 
                ch.cau_hoi, 
                ch.dap_an_a, 
                ch.dap_an_b, 
                ch.dap_an_c, 
                ch.dap_an_d, 
                ch.dap_an_dung, 
                m.De_tai, 
                m.Nguon, 
                m.Thoigian,
                ch.Nguoi_kiem_duyet_1,
                ch.Nguoi_kiem_duyet_2
            FROM 
                Cau_hoi AS ch
            JOIN 
                Mota AS m 
            ON 
                ch.maMT = m.maMT
            WHERE 
        """
        conditions = []
        params = []

        if source:
            conditions.append("m.Nguon LIKE ?")
            params.append(f"%{source}%")
        if topic != "all":
            conditions.append("m.De_tai LIKE ?")
            params.append(f"%{topic}%")
        if start_date:
            conditions.append("m.Thoigian >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("m.Thoigian <= ?")
            params.append(end_date)
        if data_type == "revised":
            conditions.append("ch.Nguoi_kiem_duyet_1 IS NOT NULL AND ch.Nguoi_kiem_duyet_2 IS NOT NULL")
        elif data_type == "unrevised":
            conditions.append("ch.Nguoi_kiem_duyet_1 IS NULL OR ch.Nguoi_kiem_duyet_2 IS NULL")


        if not conditions:
            conditions.append("1=1")

        query_sql += " AND ".join(conditions)
        print("sql: "+query_sql)
        cursor.execute(query_sql, params)

        # Lấy dữ liệu và chuyển thành danh sách các câu hỏi
        rows = cursor.fetchall()
        questions = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

        return jsonify({"success": True, "questions": questions})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

    finally:
        cursor.close()
        connection.close()



def ai_insert_data(questions, title, nguon, timestamp):
    """
    Hàm để chèn dữ liệu vào bảng Cau_hoi và Mota với định dạng mã ID (TS_1, TS_2, ...) và maMT (MTTS_1, MTTS_2, ...).
    """
    # Kết nối cơ sở dữ liệu
    connection = connect_db_ai()

    # Kiểm tra nếu không có câu hỏi để chèn
    if not questions:
        print("Không có dữ liệu để chèn vào database.")
        return 0  # Return 0 if no questions

    cursor = connection.cursor()

    # Chuyển đổi thời gian sang định dạng chuẩn SQL Server
    try:
        thoi_gian = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        formatted_timestamp = thoi_gian.strftime('%Y-%m-%d %H:%M:%S.000')
    except ValueError as e:
        print(f"Lỗi chuyển đổi thời gian: {e}")
        return 0  # Return 0 if timestamp format is invalid

    # Kiểm tra nếu metadata đã tồn tại trong bảng Mota
    check_sql = """
    SELECT MaMT FROM Mota 
    WHERE De_tai = ? AND Nguon = ? AND Thoigian = ?
    """
    cursor.execute(check_sql, (title, nguon, formatted_timestamp))
    result = cursor.fetchone()

    if result:
        maMT = result[0]
        print(f"Metadata đã tồn tại với maMT: {maMT}")
    else:
        # Tạo mã maMT mới theo định dạng MTTS_1, MTTS_2, ...
        select_sql_maMT = "SELECT MAX(CAST(SUBSTRING(MaMT, 6, LEN(MaMT)) AS INT)) FROM Mota WHERE MaMT LIKE 'MTTS_%'"
        cursor.execute(select_sql_maMT)
        max_maMT_result = cursor.fetchone()

        # Tính toán mã maMT mới
        if max_maMT_result[0] is not None:
            maMT = f"MTTS_{max_maMT_result[0] + 1}"
        else:
            maMT = "MTTS_1"  # Nếu bảng chưa có bản ghi nào

        # Thêm metadata vào bảng Mota
        insert_sql_dltt = """
        INSERT INTO Mota (MaMT, De_tai, Nguon, Thoigian) 
        VALUES (?, ?, ?, ?)
        """
        cursor.execute(insert_sql_dltt, (maMT, title, nguon, formatted_timestamp))
        connection.commit()  # Commit giao dịch để đảm bảo dữ liệu được lưu

        print(f"Đã tạo metadata mới với maMT: {maMT}")

    # Duyệt qua từng câu hỏi để chèn vào bảng Cau_hoi
    insert_sql_cau_hoi = """
    INSERT INTO Cau_hoi (ID, cau_hoi, dap_an_a, dap_an_b, dap_an_c, dap_an_d, dap_an_dung, Nguoi_kiem_duyet_1, Nguoi_kiem_duyet_2, maMT) 
    VALUES (?, ?, ?, ?, ?, ?, ?, null, null, ?)
    """

    inserted_count = 0
    for question in questions:
        try:
            cau_hoi = question.get('cauhoi')
            dap_an_a = question.get('answer_a')
            dap_an_b = question.get('answer_b')
            dap_an_c = question.get('answer_c')
            dap_an_d = question.get('answer_d')
            dap_an_dung = question.get('dapandung')

            # Kiểm tra các trường hợp null hoặc dữ liệu không hợp lệ
            if None in [cau_hoi, dap_an_a, dap_an_b, dap_an_c, dap_an_d, dap_an_dung]:
                print(f"Câu hỏi không hợp lệ và bị bỏ qua: {cau_hoi}")
                continue  # Bỏ qua câu hỏi này nếu có trường hợp null

            # Tạo mã ID mới theo định dạng TS_1, TS_2, ...
            # Lấy số lượng bản ghi hiện có trong bảng Cau_hoi
            select_sql_id = "SELECT COUNT(*) FROM Cau_hoi"
            cursor.execute(select_sql_id)
            count_result = cursor.fetchone()

            # Tính toán ID mới dựa trên số lượng hiện tại cộng thêm 1
            if count_result and count_result[0] is not None:
                new_id = f"TS_{count_result[0] + 1}"
            else:
                new_id = "TS_1"  # Nếu bảng chưa có bản ghi nào


            # Chèn câu hỏi vào bảng Cau_hoi
            cursor.execute(insert_sql_cau_hoi, (new_id, cau_hoi, dap_an_a, dap_an_b, dap_an_c, dap_an_d, dap_an_dung, maMT))
            inserted_count += 1
            print(f"Đã chèn câu hỏi: {cau_hoi} với ID: {new_id}")

        except Exception as e:
            print(f"Lỗi khi chèn câu hỏi {cau_hoi}: {e}")

    # Commit tất cả thay đổi nếu có ít nhất một câu hỏi được chèn
    if inserted_count > 0:
        connection.commit()
        print(f"Đã chèn {inserted_count}/{len(questions)} câu hỏi vào bảng Cau_hoi.")
        return inserted_count  # Return the count of inserted questions
    else:
        print("Không có câu hỏi nào được chèn vào database.")
        return 0  # Return 0 if no questions were inserted

    # Đóng kết nối
    cursor.close()
    connection.close()




@app.route('/ai_insert_data_endpoint', methods=['POST'])
def ai_insert_data_endpoint():
    data = request.get_json()
    title = data.get("topic")
    nguon = data.get("source")
    timestamp =  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    questions = data.get("questions", [])

    if not questions:
        return jsonify({"status": "failure", "message": "No questions to insert."})

    try:
        # Call ai_insert_data to perform the insert
        inserted_count = ai_insert_data(questions, title, nguon, timestamp)

        if inserted_count > 0:
            # Return a success response with a message and flag to indicate redirection
            return jsonify({
                "status": "success", 
                "message": f"Dữ liệu đã được chèn thành công, {inserted_count} câu hỏi.",
                "redirect": True  # This indicates that the frontend should redirect
            })
        else:
            return jsonify({"status": "failure", "message": "Không có câu hỏi nào được chèn."})

    except Exception as e:
        print("Error:", e)  # Log the error
        return jsonify({"status": "failure", "message": f"Data insertion failed: {str(e)}"})
    
    
    
@app.route('/app_ai')
def app_ai():
    return render_template('index_AI.html')


# Hàm kết nối với SQL Server
def tc_connect_db():
    try:
        conn = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=127.0.0.1;'    
            'DATABASE=DLTC;'      
            'UID=sa;'               
            'PWD=123456;'           
        )
        print("Kết nối tới SQL Server thành công.")
        return conn
    except pyodbc.Error as e:
        print("Lỗi kết nối tới SQL Server:", e)
        return None

# Trang chủ: hiển thị tất cả câu hỏi
# Trang chủ: hiển thị tất cả câu hỏi
@app.route('/')
@app.route('/app_tc')
def tc_index():
    connection = tc_connect_db()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu", "danger")
        return render_template('index_thucong.html', questions=[])

    cursor = connection.cursor()
    try:
        # Sử dụng JOIN để lấy thông tin từ cả hai bảng Cau_hoi và Mota
        cursor.execute("""
            SELECT 
                ch.ID, 
                ch.cau_hoi, 
                ch.dap_an_a, 
                ch.dap_an_b, 
                ch.dap_an_c, 
                ch.dap_an_d, 
                ch.dap_an_dung, 
                m.De_tai, 
                m.Nguon,
                m.Thoigian  -- Corrected query
            FROM 
                Cau_hoi AS ch
            JOIN 
                Mota AS m 
            ON 
                ch.maMT = m.maMT
        """)
        questions = cursor.fetchall()
    except Exception as e:
        flash(f"Lỗi khi truy vấn cơ sở dữ liệu: {e}", "danger")
        questions = []
    finally:
        cursor.close()
        connection.close()



    return render_template('index_thucong.html', questions=questions)

# Thêm câu hỏi
@app.route('/add_question', methods=['POST'])
def tc_add_question():
    question_data = {
        'cau_hoi': request.form.get('cau_hoi'),
        'dap_an_a': request.form.get('dap_an_a'),
        'dap_an_b': request.form.get('dap_an_b'),
        'dap_an_c': request.form.get('dap_an_c'),
        'dap_an_d': request.form.get('dap_an_d'),
        'dap_an_dung': request.form.get('dap_an_dung'),
        'de_tai': request.form.get('de_tai'),
        'nguon': request.form.get('nguon'),
        'thoi_gian': request.form.get('thoi_gian')
    }

    print("Received data:", question_data)

    # Kiểm tra dữ liệu đầu vào
    if not all(question_data.values()):
        flash("Vui lòng nhập đầy đủ thông tin.", "danger")
        return redirect(url_for('tc_index'))

    # Chuyển đổi thời gian
    try:
        thoi_gian = datetime.strptime(question_data['thoi_gian'], '%Y-%m-%dT%H:%M')
        question_data['thoi_gian'] = thoi_gian.strftime('%Y-%m-%d %H:%M:%S.000')
    except ValueError as e:
        print(f"Lỗi chuyển đổi thời gian: {e}")
        flash("Lỗi chuyển đổi thời gian, vui lòng nhập đúng định dạng.", "danger")
        return redirect(url_for('tc_index'))

    # Kết nối cơ sở dữ liệu
    connection = tc_connect_db()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu.", "danger")
        return redirect(url_for('tc_index'))

    try:
        cursor = connection.cursor()

        # Kiểm tra nếu thông tin đã tồn tại trong bảng Mota
        check_sql = """
        SELECT maMT FROM Mota 
        WHERE De_tai = ? AND Nguon = ? AND Thoigian = ?
        """
        cursor.execute(check_sql, (question_data['de_tai'], question_data['nguon'], question_data['thoi_gian']))
        result = cursor.fetchone()

        if result:
            maMT = result[0]
            print("Existing maMT found:", maMT)
        else:
            # Tạo maMT mới mà không ép kiểu int
            # Lấy maMT mới nhất từ bảng Mota
            select_max_maMT_sql = "SELECT MAX(maMT) FROM Mota"
            cursor.execute(select_max_maMT_sql)
            max_maMT_result = cursor.fetchone()

            if max_maMT_result and max_maMT_result[0]:
                # Lấy phần số sau dấu "_" và tăng lên
                max_maMT = max_maMT_result[0].split('_')[1]
                new_maMT = f"MTTC_{int(max_maMT) + 1}"
            else:
                new_maMT = "MTTC_1"  # Nếu chưa có maMT nào, bắt đầu từ 1

            maMT = new_maMT
            print("New maMT created:", maMT)

            # Thêm thông tin vào bảng Mota
            insert_sql_dltt = """
            INSERT INTO Mota (maMT, De_tai, Nguon, Thoigian) 
            VALUES (?, ?, ?, ?)
            """
            cursor.execute(insert_sql_dltt, (maMT, question_data['de_tai'], question_data['nguon'], question_data['thoi_gian']))
            connection.commit()

        # Tạo ID mới cho bảng Cau_hoi mà không ép kiểu int
       # Lấy số lượng bản ghi hiện có trong bảng Cau_hoi
            select_sql_id = "SELECT COUNT(*) FROM Cau_hoi"
            cursor.execute(select_sql_id)
            count_result = cursor.fetchone()

            # Tính toán ID mới dựa trên số lượng hiện tại cộng thêm 1
            if count_result and count_result[0] is not None:
                new_id = f"TC_{count_result[0] + 1}"
            else:
                new_id = "TC_1"  # Nếu bảng chưa có bản ghi nào


        print("New ID created:", new_id)

        # Thêm câu hỏi vào bảng Cau_hoi
        insert_sql_cau_hoi = """
        INSERT INTO Cau_hoi (ID, cau_hoi, dap_an_a, dap_an_b, dap_an_c, dap_an_d, dap_an_dung, maMT) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        values_cau_hoi = (
            new_id, question_data['cau_hoi'], question_data['dap_an_a'], question_data['dap_an_b'],
            question_data['dap_an_c'], question_data['dap_an_d'], question_data['dap_an_dung'], maMT
        )

        cursor.execute(insert_sql_cau_hoi, values_cau_hoi)
        connection.commit()
        print("Question inserted successfully:", values_cau_hoi)
        flash("Thêm câu hỏi thành công.", "success")

    except Exception as e:
        print(f"Lỗi khi thêm câu hỏi: {e}")
        flash(f"Lỗi khi thêm câu hỏi: {e}", "danger")
        connection.rollback()  # Hủy giao dịch nếu xảy ra lỗi
    finally:
        if cursor:
            cursor.close()
        connection.close()

    return redirect(url_for('tc_index'))





# Xóa câu hỏi
@app.route('/app_tc/delete_question/<id>')
def tc_delete_question(id):
    connection = tc_connect_db()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu", "danger")
        return redirect(url_for('tc_index'))

    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM Cau_hoi WHERE ID = ?", (id,))
        connection.commit()
        flash("Xóa câu hỏi thành công", "success")
    except Exception as e:
        flash(f"Lỗi khi xóa câu hỏi: {e}", "danger")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('tc_index'))

# Sửa câu hỏi
@app.route('/tc_edit_question/<id>', methods=['GET', 'POST'])
def tc_edit_question(id):
    connection = tc_connect_db()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu", "danger")
        return redirect(url_for('tc_index'))

    cursor = connection.cursor()
    if request.method == 'POST':
        question_data = {
            'cau_hoi': request.form['cau_hoi'],
            'dap_an_a': request.form['dap_an_a'],
            'dap_an_b': request.form['dap_an_b'],
            'dap_an_c': request.form['dap_an_c'],
            'dap_an_d': request.form['dap_an_d'],
            'dap_an_dung': request.form['dap_an_dung']
        }

        if not all(question_data.values()):
            flash("Tất cả các trường đều phải được điền!", "warning")
            return redirect(url_for('tc_edit_question', id=id))

        try:
            query = """
                UPDATE Cau_hoi
                SET cau_hoi = ?, dap_an_a = ?, dap_an_b = ?, dap_an_c = ?, dap_an_d = ?, dap_an_dung = ?
                WHERE ID = ?
            """
            values = (*question_data.values(), id)
            cursor.execute(query, values)
            connection.commit()
            flash("Cập nhật câu hỏi thành công", "success")
        except Exception as e:
            flash(f"Lỗi khi sửa câu hỏi: {e}", "danger")
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('tc_index'))

    # Lấy câu hỏi để sửa (khi truy cập GET)
    try:
        cursor.execute("SELECT * FROM Cau_hoi WHERE ID = ?", (id,))
        question = cursor.fetchone()
        if not question:
            flash("Câu hỏi không tồn tại", "warning")
            return redirect(url_for('tc_index'))
    except Exception as e:
        flash(f"Lỗi khi truy vấn câu hỏi: {e}", "danger")
        question = None
    finally:
        cursor.close()
        connection.close()

    return render_template('edit_question.html', question=question)

# Tìm kiếm câu hỏi
@app.route('/tc_search_questions', methods=['GET'])
def tc_search_questions():
    query = request.args.get('query', '')
    source = request.args.get('source', '')
    topic = request.args.get('topic', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Xử lý và định dạng ngày tháng
    if start_date:
        start_date = start_date.replace('T', ' ') + ":00.000"
    if end_date:
        end_date = end_date.replace('T', ' ') + ":59.999"

    connection = tc_connect_db()

    if connection is None:
        return jsonify({"success": False, "message": "Lỗi kết nối cơ sở dữ liệu"})

    cursor = connection.cursor()

    try:
        # Xây dựng câu truy vấn SQL
        query_sql = """
            SELECT 
                ch.ID, 
                ch.cau_hoi, 
                ch.dap_an_a, 
                ch.dap_an_b, 
                ch.dap_an_c, 
                ch.dap_an_d, 
                ch.dap_an_dung, 
                m.De_tai, 
                m.Nguon, 
                m.Thoigian
            FROM 
                Cau_hoi AS ch
            JOIN 
                Mota AS m 
            ON 
                ch.maMT = m.maMT
            WHERE 
        """
        conditions = []
        params = []

        if query:
            conditions.append("(ch.cau_hoi LIKE ? OR ch.ID LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        if source:
            conditions.append("m.Nguon LIKE ?")
            params.append(f"%{source}%")
        if topic != "all":
            conditions.append("m.De_tai LIKE ?")
            params.append(f"%{topic}%")
        if start_date:
            conditions.append("m.Thoigian >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("m.Thoigian <= ?")
            params.append(end_date)

        if not conditions:
            conditions.append("1=1")

        query_sql += " AND ".join(conditions)

        cursor.execute(query_sql, params)

        # Lấy dữ liệu và chuyển thành danh sách các câu hỏi
        rows = cursor.fetchall()
        questions = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

        return jsonify({"success": True, "questions": questions})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

    finally:
        cursor.close()
        connection.close()



@app.route('/app_tc')
def app_tc():
    return render_template('index_thucong.html')


def connect_db_all():
    try:
        conn = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=127.0.0.1;'    
            'DATABASE=CSDLNC;'      
            'UID=sa;'               
            'PWD=123456;'           
        )
        print("Kết nối tới SQL Server thành công.")
        return conn
    except pyodbc.Error as e:
        print("Lỗi kết nối tới SQL Server:", e)
        return None

# Trang chủ: hiển thị tất cả câu hỏi
@app.route('/app_all')
def index_all():
    connection = connect_db_all()
    if connection is None:
        flash("Lỗi kết nối cơ sở dữ liệu", "danger")
        return render_template('index_ALL.html', questions=[])

    cursor = connection.cursor()
    try:
        # Sử dụng JOIN để lấy thông tin từ cả hai bảng Cau_hoi và Mota
        cursor.execute("""
            SELECT 
                ch.ID, 
                ch.cau_hoi, 
                ch.dap_an_a, 
                ch.dap_an_b, 
                ch.dap_an_c, 
                ch.dap_an_d, 
                ch.dap_an_dung, 
                m.De_tai, 
                m.Nguon, 
                m.Thoigian,
                ch.Nguoi_kiem_duyet_1,
                ch.Nguoi_kiem_duyet_2
            FROM 
                Cau_hoi AS ch
            JOIN 
                Mota AS m 
            ON 
                ch.maMT = m.maMT
        """)
        questions = cursor.fetchall()
    except Exception as e:
        flash(f"Lỗi khi truy vấn cơ sở dữ liệu: {e}", "danger")
        questions = []
    finally:
        cursor.close()
        connection.close()
    print(questions)
    return render_template('index_ALL.html', questions=questions)


# Tìm kiếm câu hỏi
@app.route('/all_search_questions', methods=['GET'])
def all_search_questions():
    query = request.args.get('query', '')
    source = request.args.get('source', '')
    topic = request.args.get('topic', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    data_type = request.args.get('data_type', '')  # Lấy thêm data_type từ request
   
    # Xử lý và định dạng ngày tháng
    if start_date:
        start_date = start_date.replace('T', ' ') + ":00.000"
    if end_date:
        end_date = end_date.replace('T', ' ') + ":59.999"

    connection = connect_db_all()

    if connection is None:
        return jsonify({"success": False, "message": "Lỗi kết nối cơ sở dữ liệu"})

    cursor = connection.cursor()

    try:
        # Xây dựng câu truy vấn SQL
        query_sql = """
            SELECT 
                ch.ID, 
                ch.cau_hoi, 
                ch.dap_an_a, 
                ch.dap_an_b, 
                ch.dap_an_c, 
                ch.dap_an_d, 
                ch.dap_an_dung, 
                m.De_tai, 
                m.Nguon, 
                m.Thoigian,
                ch.Nguoi_kiem_duyet_1,
                ch.Nguoi_kiem_duyet_2
            FROM 
                Cau_hoi AS ch
            JOIN 
                Mota AS m 
            ON 
                ch.maMT = m.maMT
            WHERE 
        """
        conditions = []
        params = []

        # Thêm điều kiện tìm kiếm
        if query:
            conditions.append("(ch.cau_hoi LIKE ? OR ch.ID LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        if source:
            conditions.append("m.Nguon LIKE ?")
            params.append(f"%{source}%")
        if topic != "all":
            conditions.append("m.De_tai LIKE ?")
            params.append(f"%{topic}%")
        if start_date:
            conditions.append("m.Thoigian >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("m.Thoigian <= ?")
            params.append(end_date)

        # Thêm điều kiện lọc dựa trên data_type
        if data_type != "all":
            conditions.append("ch.ID LIKE ?")
            params.append(f"%{data_type}%")

        # Nếu không có điều kiện nào, thêm 1=1
        if not conditions:
            conditions.append("1=1")

        query_sql += " AND ".join(conditions)

        cursor.execute(query_sql, params)

        # Lấy dữ liệu và chuyển thành danh sách các câu hỏi
        rows = cursor.fetchall()
        questions = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

        return jsonify({"success": True, "questions": questions})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

    finally:
        cursor.close()
        connection.close()


@app.route('/app_all')
def app_all():
    return render_template('index_ALL.html') 


if __name__ == '__main__':
    app.run(debug=True, port=8080)
