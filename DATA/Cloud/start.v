import os

fn main() {
    c_file := 'hi.c'
    exe_file := 'programm.exe'

    // 1️⃣ Kompiliere die C-Datei mit dem V-TCC-Compiler
    // V nutzt intern tcc, wir gehen einfach davon aus, dass 'tcc' im PATH ist
    println('Kompiliere $c_file ...')
    compile_cmd := 'tcc $c_file -o $exe_file'
    compile_result := os.system(compile_cmd)
    if compile_result != 0 {
        println('Fehler beim Kompilieren!')
        return
    }

    // 2️⃣ Starte das C-Programm
    println('Starte $exe_file ...')
    os.system(exe_file)

    println('C-Programm beendet.')
}
