from flask import Flask, request, jsonify
from selenium import webdriver
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def batch_process_elements(driver, elements, batch_size):
    batched_elements = [elements[i:i + batch_size] for i in range(0, len(elements), batch_size)]
    computed_styles = []

    for batch in batched_elements:
        computed_styles_batch = driver.execute_script('''
            const batchedStyles = [];
            for (let i = 0; i < arguments[0].length; i++) {
                const element = arguments[0][i];
                const computedStyle = getComputedStyle(element);
                const style = {};
                for (const prop of computedStyle) {
                    style[prop] = computedStyle[prop];
                }
                batchedStyles.push({ element, style });
            }
            return batchedStyles;
        ''', batch)
        computed_styles.extend(computed_styles_batch)

    return computed_styles


@app.route('/get_computed_styles', methods=['POST'])
def get_computed_styles():
    try:
        url = request.json['url']

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--single-process")
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-breakpad")
        options.add_argument("--disable-translate")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-background-networking")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--window-size=1,1")
        


        driver = webdriver.Chrome(options=options)
        driver.get(url)

        elements = driver.find_elements('css selector', '*')

        computed_styles = batch_process_elements(driver, elements, batch_size=100)

        driver.quit()

        excluded_colors = ['rgb(0, 0, 0)', 'rgb(255, 255, 255)']
        color_counts = {}
        font_counts = {}
        font_color_counts = {}

        for style in computed_styles:
            color = style['style']['background-color']
            font = style['style']['font-family']
            font_color = style['style']['color']

            if color not in excluded_colors:
                color_counts[color] = color_counts.get(color, 0) + 1
            if font:
                font_counts[font] = font_counts.get(font, 0) + 1
            if font_color:
                font_color_counts[font_color] = font_color_counts.get(font_color, 0) + 1

        most_common_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_common_fonts = sorted(font_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_common_font_colors = sorted(font_color_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        response = {
            'Background Colors': [{'value': color, 'count': count} for color, count in most_common_colors],
            'Foreground Colors': [{'value': color, 'count': count} for color, count in most_common_font_colors],
            'Fonts': [{'value': font, 'count': count} for font, count in most_common_fonts]
        }

        return jsonify(response)
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return jsonify({'error': error_message}), 500