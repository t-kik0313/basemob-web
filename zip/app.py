from webapp import app

if __name__ == '__main__':
    print()
    print("ブラウザ確認用 URL")
    print("  トップ（選手一覧）: http://127.0.0.1:5000/players")
    print("  ルート:             http://127.0.0.1:5000/")
    print()
    app.run(debug=True, host="127.0.0.1", port=5000)
