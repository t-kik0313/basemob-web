import sqlite3

def create_database():
    conn = sqlite3.connect('baseball.db')
    c = conn.cursor()

    # 既存のplayersテーブルを削除
    c.execute('DROP TABLE IF EXISTS players')

    # ポジションと投打を追加
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            name TEXT NOT NULL,
            number INTEGER,
            image TEXT,
            main_position TEXT,
            throwing_hand TEXT,
            meet INTEGER,
            power INTEGER,
            speed INTEGER,
            arm INTEGER,
            defense INTEGER,
            catch INTEGER,
            pa INTEGER,
            h INTEGER,
            double_h INTEGER,
            triple_h INTEGER,
            hr INTEGER,
            bb INTEGER,
            hbp INTEGER,
            so INTEGER,
            sf INTEGER,
            sh INTEGER,
            rbi INTEGER,
            run INTEGER,
            sb INTEGER,
            cs INTEGER,
            dp INTEGER,
            e INTEGER
        )
    ''')

    # 初期データにポジションと投打を追加
    players_data = [
        ('山田', 10, 'yamada.png', '内野手', '右投右打', 75, 80, 70, 65, 85, 90, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ('田中', 1, 'tanaka.png', '投手', '左投左打', 85, 75, 90, 80, 75, 80, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ('佐藤', 5, 'sato.png', '外野手', '右投右打', 90, 85, 85, 95, 80, 70, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ]
    c.executemany('INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', players_data)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()