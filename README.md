# yuichan
Yui Language

## コマンドの使い方

yui file.yui
yui -i 対話モード

input.json を環境に読み込む
yui --input input.json 

ファイルYuiを実行し、環境をoutput.json に追加する 
yui file.yui --output output.json 

構文ファイルを実行して実行
yui --syntax syntax-yu.json file.yui

file.yui を--syntax-to で指定された構文に変換 (CodeVisitorを利用)
yui --syntax syntax-yu.json file.yui --syntax-to python-yui.json

mdファイルの```yui ```のコードに対し、--syntax-to で指定された構文に変換
yui --syntax syntax-yui.json file.md --syntax-to python-py.json