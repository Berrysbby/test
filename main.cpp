#include <iostream>
#include <string>
using namespace std;

string input;
int cur_i = 0;
char c = '!';

bool has_error = false;
const char END = '!';

/* служебные функции */

void read() {
    c = input[cur_i];
    cur_i++;
}

void error(const string& msg) {
    if (has_error) return;

    has_error = true;

    cout << input.substr(0, input.size() - 1) << endl;
    cout << string(cur_i - 1, ' ') << "^ " << msg << endl;
}

void set_string(const string& s) {
    input = s + "!";
    cur_i = 0;
    c = '!';
    has_error = false;
}

/* кс-грамматика */

void S();
void T();
void A();
void B();
void C();
void D();

void S() {
    read();
    T();
    if (c != END) {
        error("Лишние символы после конца выражения");
    }
}

void T() {
    if (c == '(') {
        A();
    }
    else if (c == '[') {
        B();
    }
    else {
        // ?
    }
}

void A() {
    if (c != '(') {
        error("Ожидалась '('");
        return;
    }

    read();
    T();

    if (c != ')') {
        error("Ожидалась ')'");
        return;
    }

    read();
    C();
}

void C() {
    if (c == '[') {
        B();
    }
}

void B() {
    if (c != '[') {
        error("Ожидалась '['");
        return;
    }

    read();
    T();

    if (c != ']') {
        error("Ожидалась ']'");
        return;
    }

    read();
    D();
}

void D() {
    if (c == '(') {
        A();
        D();
    }
    else if (c == '[') {
        B();
        D();
    }
}

/*
   проверка на запретное условие ")(" */

bool banned(const string& s) {
    for (int i = 0; i + 1 < s.size(); i++) {
        if (s[i] == ')' && s[i + 1] == '(')
            return true;
    }
    return false;
}


void showTask() {
    cout << "Задача: проверка правильных скобочных записей\n";
    cout << "Используются два типа скобок: () и []\n\n";

    cout << "Грамматика:\n";
    cout << "S -> T\n";
    cout << "T -> ? | A | B\n";
    cout << "A -> (T)C\n";
    cout << "C -> ? | B\n";
    cout << "B -> [T]D\n";
    cout << "D -> ? | AD | BD\n\n";

    cout << "Дополнительное ограничение:\n";
    cout << "Запрещена комбинация ')('\n\n";

    cout << "Корректные примеры:\n";
    cout << "  \n";
    cout << "  ()\n";
    cout << "  []\n";
    cout << "  ([])\n";
    cout << "  [()]\n";
    cout << "  ()[][()]\n";
    cout << "  ([][])()\n\n";

    cout << "Некорректные примеры:\n";
    cout << "  )(\n";
    cout << "  (\n";
    cout << "  [(]\n\n";

    cout << "Введите выражение для анализа\n";
    cout << "Для выхода введите: exit\n";
}


int main() {

    showTask();

    while (true) {
        string s;
        cout << "\nВведите выражение: ";
        getline(cin, s);

        if (s == "exit") {
            cout << "Завершение программы.\n";
            break;
        }

        if (banned(s)) {
            cout << "Результат: НЕВЕРНО (запрещена комбинация ')(')\n";
            continue;
        }

        set_string(s);
        S();

        if (!has_error)
            cout << "Результат: ВЕРНО\n";
        else
            cout << "Результат: НЕВЕРНО\n";
    }

    return 0;
}
