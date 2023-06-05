from flask import Flask, request, jsonify
from selenium import webdriver
from collections import Counter
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/get_computed_styles', methods=['POST'])
def get_computed_styles():
    url = request.json['url']

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/chromium-browser"   
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    computed_styles = driver.execute_script('''
        const elements = Array.from(document.querySelectorAll('*'));
        const styles = elements.map(element => {
            const computedStyle = getComputedStyle(element);
            const style = {};
            for (const prop of computedStyle) {
                style[prop] = computedStyle[prop];
            }
            return { element, style };
        });
        return styles;
    ''')

    driver.quit()

    colors = []
    fonts = []
    font_colors = []
    for style in computed_styles:
        colors.append(style['style']['background-color'])
        fonts.append(style['style']['font-family'])
        font_colors.append(style['style']['color'])

    excluded_colors = ['rgb(0, 0, 0)', 'rgb(255, 255, 255)']
    filtered_colors = [color for color in colors if color not in excluded_colors]

    color_counts = Counter(filtered_colors)

    most_common_colors = color_counts.most_common(5)
    most_common_fonts = Counter(fonts).most_common(5)
    most_common_font_colors = Counter(font_colors).most_common(5)

    response = {
    'Background Colors': [{'value': color, 'count': count} for color, count in most_common_colors],
    'Foreground Colors': [{'value': color, 'count': count} for color, count in most_common_font_colors],
    'Fonts': [{'value': font, 'count': count} for font, count in most_common_fonts]
}

    return jsonify(response)




if __name__ == '__main__':
    app.run(debug=True)
