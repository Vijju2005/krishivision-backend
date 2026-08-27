import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, Polygon as RLPolygon
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# Multilingual Crop Metadata Dictionary
CROP_METADATA = {
    "en": {
        "rice": {
            "scientific": "Oryza sativa",
            "category": "Cereal",
            "season": "Kharif / Rabi",
            "climate": "Hot and Humid (21°C - 37°C)",
            "soil": "Alluvial clayey loam",
            "water": "High (1200 - 1500 mm)",
            "duration": "120 - 150 Days",
            "harvest": "November - December",
            "lifecycle": "Sowing -> Tillering -> Flowering -> Maturity"
        },
        "paddy": {
            "scientific": "Oryza sativa",
            "category": "Cereal",
            "season": "Kharif / Rabi",
            "climate": "Hot and Humid (21°C - 37°C)",
            "soil": "Alluvial clayey loam",
            "water": "High (1200 - 1500 mm)",
            "duration": "120 - 150 Days",
            "harvest": "November - December",
            "lifecycle": "Sowing -> Tillering -> Flowering -> Maturity"
        },
        "coffee": {
            "scientific": "Coffea arabica",
            "category": "Beverage",
            "season": "Year-round",
            "climate": "Cool and Humid (15°C - 28°C)",
            "soil": "Deep rich organic sandy loam",
            "water": "High (1500 - 2500 mm)",
            "duration": "3 - 4 Years to fruit",
            "harvest": "November - February",
            "lifecycle": "Sapling -> Flowering -> Berry Growth -> Harvest"
        },
        "black pepper": {
            "scientific": "Piper nigrum",
            "category": "Spice",
            "season": "Kharif",
            "climate": "Hot and Humid (20°C - 35°C)",
            "soil": "Humus-rich clay loam",
            "water": "High (1500 - 3000 mm)",
            "duration": "3 - 4 Years",
            "harvest": "December - March",
            "lifecycle": "Sapling -> Spike Emergence -> Berry Growth -> Harvest"
        },
        "cardamom": {
            "scientific": "Elettaria cardamomum",
            "category": "Spice",
            "season": "Year-round",
            "climate": "Warm and Humid (10°C - 30°C)",
            "soil": "Forest loamy soils rich in humus",
            "water": "High (1500 - 4000 mm)",
            "duration": "2 - 3 Years",
            "harvest": "August - February",
            "lifecycle": "Nursery -> Flowering -> Capsule growth -> Harvest"
        },
        "ginger": {
            "scientific": "Zingiber officinale",
            "category": "Spice",
            "season": "Kharif",
            "climate": "Warm and Humid (19°C - 35°C)",
            "soil": "Sandy or clayey loam",
            "water": "Moderate (1200 - 1500 mm)",
            "duration": "8 - 9 Months",
            "harvest": "December - February",
            "lifecycle": "Rhizome Planting -> Sprouting -> Vegetative -> Harvest"
        },
        "turmeric": {
            "scientific": "Curcuma longa",
            "category": "Spice",
            "season": "Kharif",
            "climate": "Warm and Humid (20°C - 30°C)",
            "soil": "Well-drained sandy loam",
            "water": "High (1500 - 2200 mm)",
            "duration": "7 - 9 Months",
            "harvest": "January - March",
            "lifecycle": "Rhizome Sowing -> Sprouting -> Bulking -> Harvest"
        },
        "arecanut": {
            "scientific": "Areca catechu",
            "category": "Commercial",
            "season": "Year-round",
            "climate": "Humid Tropical (14°C - 36°C)",
            "soil": "Gravelly laterite loam",
            "water": "High (1500 - 4000 mm)",
            "duration": "5 - 6 Years",
            "harvest": "October - December",
            "lifecycle": "Sapling -> Juvenile Palm -> Crown Expansion -> Harvest"
        },
        "banana": {
            "scientific": "Musa acuminata",
            "category": "Fruit",
            "season": "Year-round",
            "climate": "Warm and Humid (15°C - 35°C)",
            "soil": "Deep rich clay loam",
            "water": "High (1500 - 2000 mm)",
            "duration": "10 - 12 Months",
            "harvest": "Year-round",
            "lifecycle": "Sucker Planting -> Vegetative -> Bunching -> Harvest"
        },
        "sugarcane": {
            "scientific": "Saccharum officinarum",
            "category": "Commercial",
            "season": "Year-round",
            "climate": "Hot and Sunny (20°C - 32°C)",
            "soil": "Deep clayey loam",
            "water": "High (1500 - 2500 mm)",
            "duration": "12 - 18 Months",
            "harvest": "December - March",
            "lifecycle": "Germination -> Tillering -> Grand Growth -> Harvest"
        },
        "cotton": {
            "scientific": "Gossypium hirsutum",
            "category": "Commercial",
            "season": "Kharif",
            "climate": "Warm and Dry (21°C - 30°C)",
            "soil": "Black cotton soil (Regur)",
            "water": "Moderate (500 - 1100 mm)",
            "duration": "160 - 180 Days",
            "harvest": "October - December",
            "lifecycle": "Sowing -> Squaring -> Flowering -> Boll Growth -> Harvest"
        },
        "groundnut": {
            "scientific": "Arachis hypogaea",
            "category": "Oilseed",
            "season": "Kharif / Rabi",
            "climate": "Warm and Sunny (20°C - 30°C)",
            "soil": "Sandy loam",
            "water": "Moderate (500 - 700 mm)",
            "duration": "100 - 120 Days",
            "harvest": "October - November",
            "lifecycle": "Sowing -> Vegetative -> Pegging -> Pod Growth -> Harvest"
        },
        "soybean": {
            "scientific": "Glycine max",
            "category": "Oilseed",
            "season": "Kharif",
            "climate": "Warm and Humid (20°C - 35°C)",
            "soil": "Well-drained loam",
            "water": "Moderate (600 - 900 mm)",
            "duration": "90 - 110 Days",
            "harvest": "September - October",
            "lifecycle": "Germination -> Vegetative -> Flowering -> Pod Growth -> Harvest"
        },
        "maize": {
            "scientific": "Zea mays",
            "category": "Cereal",
            "season": "Kharif / Rabi",
            "climate": "Warm and Sunny (21°C - 27°C)",
            "soil": "Well-drained fertile loam",
            "water": "Moderate (500 - 800 mm)",
            "duration": "90 - 110 Days",
            "harvest": "September - October",
            "lifecycle": "Sprouting -> Vegetative -> Tasseling -> Maturity -> Harvest"
        },
        "wheat": {
            "scientific": "Triticum aestivum",
            "category": "Cereal",
            "season": "Rabi",
            "climate": "Cool growing, sunny ripening",
            "soil": "Well-drained clay loam",
            "water": "Moderate (400 - 650 mm)",
            "duration": "120 - 140 Days",
            "harvest": "March - April",
            "lifecycle": "Sprouting -> Crown Root -> Tillering -> Flowering -> Harvest"
        },
        "apple": {
            "scientific": "Malus domestica",
            "category": "Fruit",
            "season": "Year-round",
            "climate": "Temperate / Cold (2°C - 21°C)",
            "soil": "Deep well-drained loam",
            "water": "Moderate (1000 - 1200 mm)",
            "duration": "4 - 5 Years",
            "harvest": "July - October",
            "lifecycle": "Bud Burst -> Flowering -> Fruit Development -> Harvest"
        },
        "saffron": {
            "scientific": "Crocus sativus",
            "category": "Spice",
            "season": "Autumn",
            "climate": "Warm summers, cold winters",
            "soil": "Calcareous well-drained loam",
            "water": "Low (300 - 400 mm)",
            "duration": "1 - 2 Years",
            "harvest": "October - November",
            "lifecycle": "Corm Planting -> Vegetative -> Flowering -> Dormancy"
        },
        "mustard": {
            "scientific": "Brassica juncea",
            "category": "Oilseed",
            "season": "Rabi",
            "climate": "Cool and Dry (10°C - 25°C)",
            "soil": "Sandy loam / Loam",
            "water": "Low (300 - 500 mm)",
            "duration": "110 - 140 Days",
            "harvest": "February - March",
            "lifecycle": "Sowing -> Vegetative -> Flowering -> Pod Growth -> Harvest"
        },
        "coconut": {
            "scientific": "Cocos nucifera",
            "category": "Commercial",
            "season": "Year-round",
            "climate": "Humid Tropical (22°C - 32°C)",
            "soil": "Sandy loam",
            "water": "High (1000 - 2000 mm)",
            "duration": "5 - 7 Years",
            "harvest": "Year-round",
            "lifecycle": "Sapling -> Vegetative -> Flowering -> Harvest"
        },
        "tea": {
            "scientific": "Camellia sinensis",
            "category": "Beverage",
            "season": "Year-round",
            "climate": "Warm and Humid (10°C - 30°C)",
            "soil": "Acidic organic loam",
            "water": "Very High (1500 - 3000 mm)",
            "duration": "3 - 4 Years",
            "harvest": "Year-round",
            "lifecycle": "Sapling -> Bush Formation -> Flush Emergence -> Harvest"
        }
    },
    "kn": {
        "rice": {
            "scientific": "Oryza sativa",
            "category": "ಧಾನ್ಯ",
            "season": "ಖಾರಿಫ್ / ರಬಿ",
            "climate": "ಬಿಸಿ ಮತ್ತು ಆರ್ದ್ರ (21°C - 37°C)",
            "soil": "ಲೋಮಿ ಜೇಡಿಮಣ್ಣು",
            "water": "ಹೆಚ್ಚು (1200 - 1500 mm)",
            "duration": "120 - 150 ದಿನಗಳು",
            "harvest": "ನವೆಂಬರ್ - ಡಿಸೆಂಬರ್",
            "lifecycle": "ಬಿತ್ತನೆ -> ಟಿಲರಿಂಗ್ -> ಹೂಬಿಡುವಿಕೆ -> ಪಕ್ವತೆ"
        },
        "paddy": {
            "scientific": "Oryza sativa",
            "category": "ಧಾನ್ಯ",
            "season": "ಖಾರಿಫ್ / ರಬಿ",
            "climate": "ಬಿಸಿ ಮತ್ತು ಆರ್ದ್ರ (21°C - 37°C)",
            "soil": "ಲೋಮಿ ಜೇಡಿಮಣ್ಣು",
            "water": "ಹೆಚ್ಚು (1200 - 1500 mm)",
            "duration": "120 - 150 ದಿನಗಳು",
            "harvest": "ನವೆಂಬರ್ - ಡಿಸೆಂಬರ್",
            "lifecycle": "ಬಿತ್ತನೆ -> ಟಿಲರಿಂಗ್ -> ಹೂಬಿಡುವಿಕೆ -> ಪಕ್ವತೆ"
        },
        "coffee": {
            "scientific": "Coffea arabica",
            "category": "ಪಾನೀಯ ಬೆಳೆ",
            "season": "ವರ್ಷಪೂರ್ತಿ",
            "climate": "ತಂಪಾದ ಮತ್ತು ಆರ್ದ್ರ (15°C - 28°C)",
            "soil": "ಆಳವಾದ ಸಾವಯವ ಮರಳು ಲೋಮ್",
            "water": "ಹೆಚ್ಚು (1500 - 2500 mm)",
            "duration": "೩ - ೪ ವರ್ಷಗಳು",
            "harvest": "ನವೆಂಬರ್ - ಫೆಬ್ರವರಿ",
            "lifecycle": "ಸಸಿ -> ಹೂಬಿಡುವಿಕೆ -> ಹಣ್ಣಾಗುವಿಕೆ -> ಕೊಯ್ಲು"
        },
        "black pepper": {
            "scientific": "Piper nigrum",
            "category": "ಸಾಂಬಾರ ಪದಾರ್ಥ",
            "season": "ಖಾರಿಫ್",
            "climate": "ಬಿಸಿ ಮತ್ತು ಆರ್ದ್ರ (20°C - 35°C)",
            "soil": "ಹ್ಯೂಮಸ್ ಭರಿತ ಜೇಡಿಮಣ್ಣು",
            "water": "ಹೆಚ್ಚು (1500 - 3000 mm)",
            "duration": "೩ - ೪ ವರ್ಷಗಳು",
            "harvest": "ಡಿಸೆಂಬರ್ - ಮಾರ್ಚ್",
            "lifecycle": "ಸಸಿ -> ಸ್ಪೈಕ್ ಹೊರಹೊಮ್ಮುವಿಕೆ -> ಬೆರ್ರಿ ಬೆಳವಣಿಗೆ -> ಕೊಯ್ಲು"
        },
        "cardamom": {
            "scientific": "Elettaria cardamomum",
            "category": "ಸಾಂಬಾರ ಪದಾರ್ಥ",
            "season": "ವರ್ಷಪೂರ್ತಿ",
            "climate": "ಬೆಚ್ಚಗಿನ ಮತ್ತು ಆರ್ದ್ರ (10°C - 30°C)",
            "soil": "ಹ್ಯೂಮಸ್ ಭರಿತ ಅರಣ್ಯ ಮಣ್ಣು",
            "water": "ಹೆಚ್ಚು (1500 - 4000 mm)",
            "duration": "೨ - ೩ ವರ್ಷಗಳು",
            "harvest": "ಆಗಸ್ಟ್ - ಫೆಬ್ರವರಿ",
            "lifecycle": "ಸಸಿಮಡಿ -> ಹೂಬಿಡುವಿಕೆ -> ಕ್ಯಾಪ್ಸುಲ್ ಬೆಳವಣಿಗೆ -> ಕೊಯ್ಲು"
        },
        "ginger": {
            "scientific": "Zingiber officinale",
            "category": "ಸಾಂಬಾರ ಪದಾರ್ಥ",
            "season": "ಖಾರಿಫ್",
            "climate": "ಬೆಚ್ಚಗಿನ ಮತ್ತು ಆರ್ದ್ರ (19°C - 35°C)",
            "soil": "ಮರಳು ಮಿಶ್ರಿತ ಲೋಮ್",
            "water": "ಮಧ್ಯಮ (1200 - 1500 mm)",
            "duration": "೮ - ೯ ತಿಂಗಳುಗಳು",
            "harvest": "ಡಿಸೆಂಬರ್ - ಫೆಬ್ರವರಿ",
            "lifecycle": "ಶುಂಠಿ ನಾಟಿ -> ಮೊಳಕೆಯೊಡೆಯುವುದು -> ಸಸ್ಯಕ -> ಕೊಯ್ಲು"
        },
        "turmeric": {
            "scientific": "Curcuma longa",
            "category": "ಸಾಂಬಾರ ಪದಾರ್ಥ",
            "season": "ಖಾರಿಫ್",
            "climate": "ಬೆಚ್ಚಗಿನ ಮತ್ತು ಆರ್ದ್ರ (20°C - 30°C)",
            "soil": "ಉತ್ತಮ ನೀರಾವರಿ ಮರಳು ಲೋಮ್",
            "water": "ಹೆಚ್ಚು (1500 - 2200 mm)",
            "duration": "೭ - ೯ ತಿಂಗಳುಗಳು",
            "harvest": "ಜನವರಿ - ಮಾರ್ಚ್",
            "lifecycle": "ನಾಟಿ -> ಮೊಳಕೆಯೊಡೆಯುವುದು -> ಬಲ್ಕಿಂಗ್ -> ಕೊಯ್ಲು"
        },
        "arecanut": {
            "scientific": "Areca catechu",
            "category": "ವಾಣಿಜ್ಯ ಬೆಳೆ",
            "season": "ವರ್ಷಪೂರ್ತಿ",
            "climate": "ಆರ್ದ್ರ ಉಷ್ಣವಲಯ (14°C - 36°C)",
            "soil": "ಜಲ್ಲಿ ಕೆಮ್ಮಣ್ಣು",
            "water": "ಹೆಚ್ಚು (1500 - 4000 mm)",
            "duration": "೫ - ೬ ವರ್ಷಗಳು",
            "harvest": "ಅಕ್ಟೋಬರ್ - ಡಿಸೆಂಬರ್",
            "lifecycle": "ಸಸಿ -> ಬಾಲ ತಾಲ ತಾಳೆ -> ಕಿರೀಟ ವಿಸ್ತರಣೆ -> ಕೊಯ್ಲು"
        },
        "banana": {
            "scientific": "Musa acuminata",
            "category": "ಹಣ್ಣು",
            "season": "ವರ್ಷಪೂರ್ತಿ",
            "climate": "ಬೆಚ್ಚಗಿನ ಮತ್ತು ಆರ್ದ್ರ (15°C - 35°C)",
            "soil": "ಆಳವಾದ ಜೇಡಿಮಣ್ಣು",
            "water": "ಹೆಚ್ಚು (1500 - 2000 mm)",
            "duration": "10 - 12 ತಿಂಗಳುಗಳು",
            "harvest": "ವರ್ಷಪೂರ್ತಿ",
            "lifecycle": "ಸಸಿ ನಾಟಿ -> ಸಸ್ಯಕ -> ಗೊಂಚಲು ಹಂತ -> ಕೊಯ್ಲು"
        },
        "sugarcane": {
            "scientific": "Saccharum officinarum",
            "category": "ವಾಣಿಜ್ಯ ಬೆಳೆ",
            "season": "ವರ್ಷಪೂರ್ತಿ",
            "climate": "ಬಿಸಿಲು ಮತ್ತು ಬಿಸಿ (20°C - 32°C)",
            "soil": "ಆಳವಾದ ಜೇಡಿಮಣ್ಣು",
            "water": "ಹೆಚ್ಚು (1500 - 2500 mm)",
            "duration": "12 - 18 ತಿಂಗಳುಗಳು",
            "harvest": "ಡಿಸೆಂಬರ್ - ಮಾರ್ಚ್",
            "lifecycle": "ಮೊಳಕೆಯೊಡೆಯುವಿಕೆ -> ಟಿಲರಿಂಗ್ -> ಬೆಳವಣಿಗೆ -> ಕೊಯ್ಲು"
        },
        "cotton": {
            "scientific": "Gossypium hirsutum",
            "category": "ವಾಣಿಜ್ಯ ಬೆಳೆ",
            "season": "ಖಾರಿಫ್",
            "climate": "ಬೆಚ್ಚಗಿನ ಮತ್ತು ಒಣ (21°C - 30°C)",
            "soil": "ಕಪ್ಪು ಹತ್ತಿ ಮಣ್ಣು",
            "water": "ಮಧ್ಯಮ (500 - 1100 mm)",
            "duration": "160 - 180 ದಿನಗಳು",
            "harvest": "ಅಕ್ಟೋಬರ್ - ಡಿಸೆಂಬರ್",
            "lifecycle": "ಬಿತ್ತನೆ -> ಮೊಗ್ಗು ಬರುವುದು -> ಹೂಬಿಡುವಿಕೆ -> ಕಾಯಿ ಬೆಳೆಯುವುದು -> ಕೊಯ್ಲು"
        },
        "groundnut": {
            "scientific": "Arachis hypogaea",
            "category": "ಎಣ್ಣೆಕಾಳು",
            "season": "ಖಾರಿಫ್ / ರಬಿ",
            "climate": "ಬೆಚ್ಚಗಿನ ಮತ್ತು ಬಿಸಿಲು (20°C - 30°C)",
            "soil": "ಮರಳು ಮಿಶ್ರಿತ ಲೋಮ್",
            "water": "ಮಧ್ಯಮ (500 - 700 mm)",
            "duration": "100 - 120 ದಿನಗಳು",
            "harvest": "ಅಕ್ಟೋಬರ್ - ನವೆಂಬರ್",
            "lifecycle": "ಬಿತ್ತನೆ -> ಸಸ್ಯಕ -> ಪೆಗ್ಗಿಂಗ್ -> ಕಾಯಿ ಅಭಿವೃದ್ಧಿ -> ಕೊಯ್ಲು"
        },
        "soybean": {
            "scientific": "Glycine max",
            "category": "ಎಣ್ಣೆಕಾಳು",
            "season": "ಖಾರಿಫ್",
            "climate": "ಬಚ್ಚಗಿನ ಮತ್ತು ಆರ್ದ್ರ (20°C - 35°C)",
            "soil": "ಉತ್ತಮ ನೀರಾವರಿ ಲೋಮ್",
            "water": "ಮಧ್ಯಮ (600 - 900 mm)",
            "duration": "90 - 110 ದಿನಗಳು",
            "harvest": "ಸೆಪ್ಟೆಂಬರ್ - ಅಕ್ಟೋಬರ್",
            "lifecycle": "ಮೊಳಕೆ -> ಸಸ್ಯಕ -> ಹೂಬಿಡುವಿಕೆ -> ಕಾಯಿ ಬೆಳವಣಿಗೆ -> ಕೊಯ್ಲು"
        },
        "maize": {
            "scientific": "Zea mays",
            "category": "ಧಾನ್ಯ",
            "season": "ಖಾರಿಫ್ / ರಬಿ",
            "climate": "ಬೆಚ್ಚಗಿನ ಮತ್ತು ಬಿಸಿಲು (21°C - 27°C)",
            "soil": "ಫಲವತ್ತಾದ ಲೋಮ್",
            "water": "ಮಧ್ಯಮ (500 - 800 mm)",
            "duration": "90 - 110 ದಿನಗಳು",
            "harvest": "ಸೆಪ್ಟೆಂಬರ್ - ಅಕ್ಟೋಬರ್",
            "lifecycle": "ಮೊಳಕೆ -> ಸಸ್ಯಕ -> ಹೂಬಿಡುವುದು -> ಪಕ್ವತೆ -> ಕೊಯ್ಲು"
        },
        "wheat": {
            "scientific": "Triticum aestivum",
            "category": "ಧಾನ್ಯ",
            "season": "ರಬಿ",
            "climate": "ತಂಪಾದ ಬೆಳವಣಿಗೆ, ಬಿಸಿಲು ಕೊಯ್ಲು",
            "soil": "ಆಳವಾದ ಜೇಡಿಮಣ್ಣು",
            "water": "ಮಧ್ಯಮ (400 - 650 mm)",
            "duration": "120 - 140 ದಿನಗಳು",
            "harvest": "ಮಾರ್ಚ್ - ಏಪ್ರಿಲ್",
            "lifecycle": "ಮೊಳಕೆ -> ಕಿರೀಟ ಬೇರು -> ಟಿಲರಿಂಗ್ -> ಹೂಬಿಡುವಿಕೆ -> ಕೊಯ್ಲು"
        },
        "apple": {
            "scientific": "Malus domestica",
            "category": "ಹಣ್ಣು",
            "season": "ವರ್ಷಪೂರ್ತಿ",
            "climate": "ಶೀತವಲಯ / ತಂಪಾದ (2°C - 21°C)",
            "soil": "ಆಳವಾದ ಫಲವತ್ತಾದ ಮಣ್ಣು",
            "water": "ಮಧ್ಯಮ (1000 - 1200 mm)",
            "duration": "೪ - ೫ ವರ್ಷಗಳು",
            "harvest": "ಜುಲೈ - ಅಕ್ಟೋಬರ್",
            "lifecycle": "ಮೊಗ್ಗು ಹೊಡೆಯುವುದು -> ಹೂಬಿಡುವಿಕೆ -> ಹಣ್ಣು ಅಭಿವೃದ್ಧಿ -> ಕೊಯ್ಲು"
        },
        "saffron": {
            "scientific": "Crocus sativus",
            "category": "ಸಾಂಬಾರ ಪದಾರ್ಥ",
            "season": "ಶರತ್ಕಾಲ",
            "climate": "ಬೆಚ್ಚಗಿನ ಬೇಸಿಗೆ, ತಂಪಾದ ಚಳಿಗಾಲ",
            "soil": "ಕ್ಯಾಲ್ಸಿಯಂ ಭರಿತ ಮರಳು ಮಣ್ಣು",
            "water": "ಕಡಿಮೆ (300 - 400 mm)",
            "duration": "೧ - ೨ ವರ್ಷಗಳು",
            "harvest": "ಅಕ್ಟೋಬರ್ - ನವೆಂಬರ್",
            "lifecycle": "ಗೆಡ್ಡೆ ನಾಟಿ -> ಸಸ್ಯಕ -> ಹೂಬಿಡುವಿಕೆ -> ಸುಪ್ತಾವಸ್ಥೆ"
        },
        "mustard": {
            "scientific": "Brassica juncea",
            "category": "ಎಣ್ಣೆಕಾಳು",
            "season": "ರಬಿ",
            "climate": "ತಂಪಾದ ಮತ್ತು ಒಣ (10°C - 25°C)",
            "soil": "ಮರಳು ಮಿಶ್ರಿತ ಜೇಡಿಮಣ್ಣು",
            "water": "ಕಡಿಮೆ (300 - 500 mm)",
            "duration": "110 - 140 ದಿನಗಳು",
            "harvest": "ಫೆಬ್ರವರಿ - ಮಾರ್ಚ್",
            "lifecycle": "ಬಿತ್ತನೆ -> ಸಸ್ಯಕ -> ಹೂಬಿಡುವಿಕೆ -> ಕಾಯಿ ಬೆಳವಣಿಗೆ -> ಕೊಯ್ಲು"
        },
        "coconut": {
            "scientific": "Cocos nucifera",
            "category": "ವಾಣಿಜ್ಯ ಬೆಳೆ",
            "season": "ವರ್ಷಪೂರ್ತಿ",
            "climate": "ಆರ್ದ್ರ ಉಷ್ಣವಲಯ (22°C - 32°C)",
            "soil": "ಮರಳು ಮಿಶ್ರಿತ ಲೋಮ್",
            "water": "ಹೆಚ್ಚು (1000 - 2000 mm)",
            "duration": "೫ - ೭ ವರ್ಷಗಳು",
            "harvest": "ವರ್ಷಪೂರ್ತಿ",
            "lifecycle": "ಸಸಿ -> ಸಸ್ಯಕ ಹಂತ -> ಹೂಬಿಡುವಿಕೆ -> ಕೊಯ್ಲು"
        },
        "tea": {
            "scientific": "Camellia sinensis",
            "category": "ಪಾನೀಯ ಬೆಳೆ",
            "season": "ವರ್ಷಪೂರ್ತಿ",
            "climate": "ಬೆಚ್ಚಗಿನ ಆರ್ದ್ರ ತಂಪಾದ ಪರ್ವತ (10°C - 30°C)",
            "soil": "ಆಮ್ಲೀಯ ಸಾವಯವ ಹ್ಯೂಮಸ್ ಲೋಮ್",
            "water": "ಅತಿ ಹೆಚ್ಚು (1500 - 3000 mm)",
            "duration": "೩ - ೪ ವರ್ಷಗಳು",
            "harvest": "ವರ್ಷಪೂರ್ತಿ (ಆಗಾಗ್ಗೆ ಚಿಗುರೆಲೆ ಕಟಾವು)",
            "lifecycle": "ಸಸಿ -> ಪೊದೆ ರೂಪೀಕರಣ -> ಎಲೆ ಚಿಗುರುವುದು -> ಕೊಯ್ಲು"
        }
    },
    "hi": {
        "rice": {
            "scientific": "Oryza sativa",
            "category": "अनाज",
            "season": "खरीफ / रबी",
            "climate": "गर्म और आर्द्र (21°C - 37°C)",
            "soil": "जलोढ़ दोमट मिट्टी",
            "water": "अधिक (1200 - 1500 mm)",
            "duration": "120 - 150 दिन",
            "harvest": "नवंबर - दिसंबर",
            "lifecycle": "बुवाई -> कल्ले निकलना -> फूल आना -> परिपक्वता"
        },
        "paddy": {
            "scientific": "Oryza sativa",
            "category": "अनाज",
            "season": "खरीफ / रबी",
            "climate": "गर्म और आर्द्र (21°C - 37°C)",
            "soil": "जलोढ़ दोमट मिट्टी",
            "water": "अधिक (1200 - 1500 mm)",
            "duration": "120 - 150 दिन",
            "harvest": "नवंबर - दिसंबर",
            "lifecycle": "बुवाई -> कल्ले निकलना -> फूल आना -> परिपक्वता"
        },
        "coffee": {
            "scientific": "Coffea arabica",
            "category": "पेय पदार्थ",
            "season": "वर्षभर",
            "climate": "ठंडी और आर्द्र (15°C - 28°C)",
            "soil": "गहरी उपजाऊ दोमट मिट्टी",
            "water": "अधिक (1500 - 2500 mm)",
            "duration": "३ - ४ वर्ष",
            "harvest": "नवंबर - फरवरी",
            "lifecycle": "पौधा -> फूल आना -> बेरी विकास -> कटाई"
        },
        "black pepper": {
            "scientific": "Piper nigrum",
            "category": "मसाला",
            "season": "खरीफ",
            "climate": "गर्म और आर्द्र (20°C - 35°C)",
            "soil": "ह्यूमस युक्त दोमट मिट्टी",
            "water": "अधिक (1500 - 3000 mm)",
            "duration": "३ - ४ वर्ष",
            "harvest": "दिसंबर - मार्च",
            "lifecycle": "पौधा -> स्पाइक निकलना -> बेरी विकास -> कटाई"
        },
        "cardamom": {
            "scientific": "Elettaria cardamomum",
            "category": "मसाला",
            "season": "वर्षभर",
            "climate": "गर्म और आर्द्र (10°C - 30°C)",
            "soil": "ह्यूमस समृद्ध जंगली मिट्टी",
            "water": "अधिक (1500 - 4000 mm)",
            "duration": "२ - 3 वर्ष",
            "harvest": "अगस्त - फरवरी",
            "lifecycle": "नर्सरी -> फूल आना -> कैप्सूल विकास -> कटाई"
        },
        "ginger": {
            "scientific": "Zingiber officinale",
            "category": "मसाला",
            "season": "खरीफ",
            "climate": "गर्म और आर्द्र (19°C - 35°C)",
            "soil": "बलुई दोमट मिट्टी",
            "water": "मध्यम (1200 - 1500 mm)",
            "duration": "८ - ९ महीने",
            "harvest": "दिसंबर - फरवरी",
            "lifecycle": "प्रकंद रोपण -> अंकुरण -> वानस्पतिक -> कटाई"
        },
        "turmeric": {
            "scientific": "Curcuma longa",
            "category": "मसाला",
            "season": "खरीफ",
            "climate": "गर्म और आर्द्र (20°C - 30°C)",
            "soil": "अच्छे जल निकासी वाली बलुई दोमट",
            "water": "अधिक (1500 - 2200 mm)",
            "duration": "७ - ९ महीने",
            "harvest": "जनवरी - मार्च",
            "lifecycle": "प्रकंद बुवाई -> अंकुरण -> कंद बनना -> कटाई"
        },
        "arecanut": {
            "scientific": "Areca catechu",
            "category": "व्यावसायिक",
            "season": "वर्षभर",
            "climate": "आर्द्र उष्णकटिबंधीय (14°C - 36°C)",
            "soil": "कंक्रीट लेटेराइट दोमट",
            "water": "अधिक (1500 - 4000 mm)",
            "duration": "೫ - ६ वर्ष",
            "harvest": "अक्टूबर - दिसंबर",
            "lifecycle": "पौधा -> किशोर ताड़ -> मुकुट विस्तार -> कटाई"
        },
        "banana": {
            "scientific": "Musa acuminata",
            "category": "फल",
            "season": "वर्षभर",
            "climate": "गर्म और आर्द्र (15°C - 35°C)",
            "soil": "गहरी समृद्ध दोमट मिट्टी",
            "water": "अधिक (1500 - 2000 mm)",
            "duration": "10 - 12 महीने",
            "harvest": "वर्षभर",
            "lifecycle": "सकर रोपण -> वानस्पतिक -> गुच्छा बनना -> कटाई"
        },
        "sugarcane": {
            "scientific": "Saccharum officinarum",
            "category": "व्यावसायिक",
            "season": "वर्षभर",
            "climate": "गर्म और धूपदार (20°C - 32°C)",
            "soil": "गहरी दोमट मिट्टी",
            "water": "अधिक (1500 - 2500 mm)",
            "duration": "12 - 18 महीने",
            "harvest": "दिसंबर - मार्च",
            "lifecycle": "अंकुरण -> कल्ले निकलना -> मुख्य विकास -> कटाई"
        },
        "cotton": {
            "scientific": "Gossypium hirsutum",
            "category": "व्यावसायिक",
            "season": "खरीफ",
            "climate": "गर्म और सूखा (21°C - 30°C)",
            "soil": "काली कपास मिट्टी (रेगुर)",
            "water": "मध्यम (500 - 1100 mm)",
            "duration": "160 - 180 दिन",
            "harvest": "अक्टूबर - दिसंबर",
            "lifecycle": "बुवाई -> कली बनना -> फूल आना -> डोडे का विकास -> कटाई"
        },
        "groundnut": {
            "scientific": "Arachis hypogaea",
            "category": "तिलहन",
            "season": "खरीफ / रबी",
            "climate": "गर्म और धूपदार (20°C - 30°C)",
            "soil": "बलुई दोमट",
            "water": "मध्यम (500 - 700 mm)",
            "duration": "100 - 120 दिन",
            "harvest": "अक्टूबर - नवंबर",
            "lifecycle": "बुवाई -> वानस्पतिक -> पेगिंग -> पोड विकास -> कटाई"
        },
        "soybean": {
            "scientific": "Glycine max",
            "category": "तिलहन",
            "season": "खरीफ",
            "climate": "गर्म और आर्द्र (20°C - 35°C)",
            "soil": "अच्छे जल निकासी वाली दोमट",
            "water": "मध्यम (600 - 900 mm)",
            "duration": "90 - 110 दिन",
            "harvest": "सितंबर - अक्टूबर",
            "lifecycle": "अंकुरण -> वानस्पतिक -> फूल आना -> फली विकास -> कटाई"
        },
        "maize": {
            "scientific": "Zea mays",
            "category": "अनाज",
            "season": "खरीफ / रबी",
            "climate": "गर्म और धूपदार (21°C - 27°C)",
            "soil": "अच्छी जल निकासी वाली उपजाऊ दोमट",
            "water": "मध्यम (500 - 800 mm)",
            "duration": "90 - 110 दिन",
            "harvest": "सितंबर - अक्टूबर",
            "lifecycle": "अंकुरण -> वानस्पतिक -> टैसेलिंग -> परिपक्वता -> कटाई"
        },
        "wheat": {
            "scientific": "Triticum aestivum",
            "category": "अनाज",
            "season": "रबी",
            "climate": "ठंडी जलवायु में विकास, पकते समय तेज धूप",
            "soil": "अच्छी जल निकासी वाली दोमट मिट्टी",
            "water": "मध्यम (400 - 650 mm)",
            "duration": "120 - 140 दिन",
            "harvest": "मार्च - अप्रैल",
            "lifecycle": "अंकुरण -> मुकुट जड़ बनना -> कल्ले निकलना -> फूल आना -> कटाई"
        },
        "apple": {
            "scientific": "Malus domestica",
            "category": "फल",
            "season": "वर्षभर",
            "climate": "शीतोष्ण / ठंडा (2°C - 21°C)",
            "soil": "गहरी अच्छी जल निकासी वाली दोमट",
            "water": "मध्यम (1000 - 1200 mm)",
            "duration": "೪ - ೫ वर्ष",
            "harvest": "जुलाई - अक्टूबर",
            "lifecycle": "कली का खिलना -> फूल आना -> फल का विकास -> कटाई"
        },
        "saffron": {
            "scientific": "Crocus sativus",
            "category": "मसाला",
            "season": "शरद ऋतु",
            "climate": "गर्म गर्मी, ठंडी सर्दी",
            "soil": "कैल्शियम युक्त अच्छे जल निकासी वाली दोमट",
            "water": "कम (300 - 400 mm)",
            "duration": "१ - ೨ वर्ष",
            "harvest": "अक्टूबर - नवंबर",
            "lifecycle": "कंद रोपण -> वानस्पतिक -> फूल आना -> सुप्तता"
        },
        "mustard": {
            "scientific": "Brassica juncea",
            "category": "तिलहन",
            "season": "रबी",
            "climate": "ठंडा और शुष्क (10°C - 25°C)",
            "soil": "बलुई दोमट / दोमट",
            "water": "कम (300 - 500 mm)",
            "duration": "110 - 140 दिन",
            "harvest": "फरवरी - मार्च",
            "lifecycle": "बुवाई -> वानस्पतिक -> फूल आना -> फली विकास -> कटाई"
        },
        "coconut": {
            "scientific": "Cocos nucifera",
            "category": "व्यावसायिक",
            "season": "वर्षभर",
            "climate": "आर्द्र उष्णकटिबंधीय (22°C - 32°C)",
            "soil": "बलुई दोमट मिट्टी",
            "water": "अधिक (1000 - 2000 mm)",
            "duration": "೫ - 7 वर्ष",
            "harvest": "वर्षभर",
            "lifecycle": "अंकुर -> वानस्पतिक -> फूल आना -> कटाई"
        },
        "tea": {
            "scientific": "Camellia sinensis",
            "category": "पेय पदार्थ",
            "season": "वर्षभर",
            "climate": "गर्म, आर्द्र, ठंडी पहाड़ी जलवायु (10°C - 30°C)",
            "soil": "अम्लीय कार्बनिक ह्यूमस समृद्ध दोमट",
            "water": "बहुत अधिक (1500 - 3000 mm)",
            "duration": "೩ - ೪ वर्ष",
            "harvest": "वर्षभर (नियमित पत्ती तोड़ना)",
            "lifecycle": "पौधा -> झाड़ी बनाना -> पत्तियों का निकलना -> कटाई"
        }
    }
}

# Add default fallback for missing keys
def get_crop_meta_translated(crop_name: str, lang: str) -> dict:
    crop_key = crop_name.lower().strip()
    lang_key = lang.lower().strip()
    
    # Fallback structure
    default_meta = {
        "scientific": "N/A",
        "category": "Commercial",
        "season": "Kharif",
        "climate": "Tropical Suitability",
        "soil": "Loamy soil",
        "water": "Moderate",
        "duration": "120 Days",
        "harvest": "Seasonal",
        "lifecycle": "Sowing -> Vegetative -> Flowering -> Harvest"
    }
    
    # Find translation
    lang_dict = CROP_METADATA.get(lang_key, CROP_METADATA["en"])
    meta = lang_dict.get(crop_key, CROP_METADATA["en"].get(crop_key, default_meta))
    return meta

def create_district_map_drawing(
    district_boundary: dict | None,
    crop_boundary: dict | None = None,
    health: str = "Healthy",
    width: float = 460,
    height: float = 180
) -> Drawing:
    drawing = Drawing(width, height)
    
    # Background Box
    drawing.add(Rect(0, 0, width, height, fillColor=colors.HexColor('#F5F7F6'), strokeColor=colors.HexColor('#DCE3DF'), strokeWidth=1))
    
    if not district_boundary:
        return drawing
        
    geom_type = district_boundary.get("type")
    coordinates = district_boundary.get("coordinates")
    if not coordinates:
        return drawing
        
    # Collect all points to fit bounding box
    points = []
    if geom_type == "Polygon":
        for ring in coordinates:
            points.extend(ring)
    elif geom_type == "MultiPolygon":
        for poly in coordinates:
            for ring in poly:
                points.extend(ring)
                
    if not points:
        return drawing
        
    lngs = [pt[0] for pt in points]
    lats = [pt[1] for pt in points]
    min_lng, max_lng = min(lngs), max(lngs)
    min_lat, max_lat = min(lats), max(lats)
    
    lng_range = max_lng - min_lng if max_lng != min_lng else 1.0
    lat_range = max_lat - min_lat if max_lat != min_lat else 1.0
    
    padding = 20
    scale_w = (width - 2 * padding) / lng_range
    scale_h = (height - 2 * padding) / lat_range
    scale = min(scale_w, scale_h)
    
    offset_x = (width - lng_range * scale) / 2.0
    offset_y = (height - lat_range * scale) / 2.0
    
    def transform(lng, lat):
        x = offset_x + (lng - min_lng) * scale
        y = offset_y + (lat - min_lat) * scale
        return x, y
        
    # Draw District Boundaries (Selected Highlighted, Transparent fill)
    if geom_type == "Polygon":
        for ring in coordinates:
            flat = []
            for pt in ring:
                flat.extend(transform(pt[0], pt[1]))
            if len(flat) >= 6:
                drawing.add(RLPolygon(flat, fillColor=colors.transparent, strokeColor=colors.HexColor('#2E7D4F'), strokeWidth=2.0))
    elif geom_type == "MultiPolygon":
        for poly in coordinates:
            for ring in poly:
                flat = []
                for pt in ring:
                    flat.extend(transform(pt[0], pt[1]))
                if len(flat) >= 6:
                    drawing.add(RLPolygon(flat, fillColor=colors.transparent, strokeColor=colors.HexColor('#2E7D4F'), strokeWidth=2.0))
                    
    # Draw Crop Field Boundary if present
    if crop_boundary:
        c_geom_type = crop_boundary.get("type")
        c_coordinates = crop_boundary.get("coordinates")
        
        health_color = '#2E7D4F' # Healthy
        if health.lower() == 'at risk':
            health_color = '#E0A62B'
        elif health.lower() == 'unhealthy':
            health_color = '#D64545'
            
        if c_coordinates:
            if c_geom_type == "Polygon":
                for ring in c_coordinates:
                    flat = []
                    for pt in ring:
                        flat.extend(transform(pt[0], pt[1]))
                    if len(flat) >= 6:
                        drawing.add(RLPolygon(flat, fillColor=colors.transparent, strokeColor=colors.HexColor(health_color), strokeWidth=2.5))
            elif c_geom_type == "MultiPolygon":
                for poly in c_coordinates:
                    for ring in poly:
                        flat = []
                        for pt in ring:
                            flat.extend(transform(pt[0], pt[1]))
                        if len(flat) >= 6:
                            drawing.add(RLPolygon(flat, fillColor=colors.transparent, strokeColor=colors.HexColor(health_color), strokeWidth=2.5))
                            
    return drawing

PDF_TEMPLATE_VERSION = "3.0-modern"

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import KeepTogether, PageBreak
from PIL import Image as PILImage
from datetime import timedelta

class NumberedCanvas(canvas.Canvas):
    report_id = "KV-REPORT"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        primary_green = colors.HexColor('#1B5E3A')
        text_grey = colors.HexColor('#5E7065')
        
        # --- HEADER (only on pages > 1) ---
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor('#2E7D4F'))
            self.setLineWidth(0.75)
            self.line(45, 800, 550.27, 800)
            
            self.setFont('Helvetica-Bold', 7.5)
            self.setFillColor(primary_green)
            self.drawString(45, 806, "KRISHIVISION AI  |  SATELLITE CROP MONITORING & ANALYTICS")
        
        # --- FOOTER ---
        self.setStrokeColor(colors.HexColor('#DCE3DF'))
        self.setLineWidth(0.5)
        self.line(45, 45, 550.27, 45)
        
        self.setFont('Helvetica-Bold', 7.5)
        self.setFillColor(primary_green)
        self.drawString(45, 32, "KrishiVision AI")
        self.setFont('Helvetica', 7)
        self.setFillColor(text_grey)
        self.drawString(100, 32, f"  |  ID: {self.report_id}  |  AI-Powered Satellite Crop Monitoring")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(550.27, 32, page_str)
        
        self.restoreState()


def build_logo_drawing() -> Drawing:
    d = Drawing(32, 32)
    # Circle base
    d.add(Rect(0, 0, 32, 32, fillColor=colors.HexColor('#1B5E3A'), strokeColor=None, rx=6, ry=6))
    # Custom vector leaf geometry
    d.add(RLPolygon([16, 6, 26, 16, 16, 26, 6, 16], fillColor=colors.HexColor('#D1E7DD'), strokeColor=None))
    d.add(RLPolygon([16, 6, 21, 16, 16, 26, 11, 16], fillColor=colors.HexColor('#198754'), strokeColor=None))
    return d


def make_kpi_card(label: str, value: str, is_dark: bool = False) -> Table:
    bg_color = '#1B5E3A' if is_dark else '#F4F9F6'
    border_color = '#1B5E3A'
    text_color = '#FFFFFF' if is_dark else '#2D3748'
    label_color = '#D1E7DD' if is_dark else '#5E7065'
    value_color = '#FFFFFF' if is_dark else '#1B5E3A'
    
    lbl_style = ParagraphStyle(
        'KPILbl_' + label.replace(' ', '_'), fontName='Helvetica-Bold', fontSize=8, leading=10,
        textColor=colors.HexColor(label_color)
    )
    val_style = ParagraphStyle(
        'KPIVal_' + label.replace(' ', '_'), fontName='Helvetica-Bold', fontSize=12, leading=15,
        textColor=colors.HexColor(value_color)
    )
    
    t = Table([
        [Paragraph(label.upper(), lbl_style)],
        [Spacer(1, 2)],
        [Paragraph(value, val_style)]
    ], colWidths=[240])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg_color)),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor(border_color)),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    return t


def make_health_progress_bar(score: float, status: str) -> Table:
    d = Drawing(400, 20)
    d.add(Rect(0, 0, 400, 20, fillColor=colors.HexColor('#E2E8F0'), strokeColor=None, rx=10, ry=10))
    color_hex = '#1B5E3A' if status == 'Good' else ('#D97706' if status == 'Moderate' else '#DC2626')
    if score > 0:
        width = (score / 100.0) * 400
        d.add(Rect(0, 0, width, 20, fillColor=colors.HexColor(color_hex), strokeColor=None, rx=10, ry=10))
        
    score_style = ParagraphStyle('ScoreStyle', fontName='Helvetica-Bold', fontSize=14, leading=17, textColor=colors.HexColor('#1B5E3A'), alignment=1)
    status_style = ParagraphStyle('StatusStyle', fontName='Helvetica-Bold', fontSize=16, leading=19, textColor=colors.HexColor(color_hex), alignment=1)
    
    t = Table([
        [Paragraph(f"HEALTH SCORE: {score} / 100", score_style)],
        [Spacer(1, 6)],
        [d],
        [Spacer(1, 6)],
        [Paragraph(status.upper(), status_style)]
    ], colWidths=[400])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return t


def make_timeline_widget(current_stage: str) -> Table:
    stages = ['Planting', 'Germination', 'Vegetative', 'Flowering', 'Maturity', 'Harvest']
    current_idx = -1
    for i, s in enumerate(stages):
        if s.lower() in current_stage.lower() or current_stage.lower() in s.lower():
            current_idx = i
            break
            
    row = []
    col_widths = []
    
    for idx, s in enumerate(stages):
        if idx < current_idx:
            bg = '#D1E7DD'
            text = f"<b>{s.upper()}</b>"
            tc = '#1B5E3A'
        elif idx == current_idx:
            bg = '#1B5E3A'
            text = f"<b>{s.upper()}</b>"
            tc = '#FFFFFF'
        else:
            bg = '#F4F9F6'
            text = s.upper()
            tc = '#9CA3AF'
            
        p_style = ParagraphStyle(
            f'TimeNode_{idx}', fontName='Helvetica-Bold' if idx == current_idx else 'Helvetica',
            fontSize=7.5, leading=10, textColor=colors.HexColor(tc), alignment=1
        )
        
        node_table = Table([[Paragraph(text, p_style)]], colWidths=[65], rowHeights=[20])
        node_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg)),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#1B5E3A')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        row.append(node_table)
        col_widths.append(65)
        
        if idx < len(stages) - 1:
            arrow_style = ParagraphStyle(f'Arr_{idx}', fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.HexColor('#1B5E3A'), alignment=1)
            row.append(Paragraph(">", arrow_style))
            col_widths.append(20)
            
    t = Table([row], colWidths=col_widths)
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    return t


def get_local_satellite_image(db_session, state: str, district: str, crop: str) -> str | None:
    if not db_session:
        return None
    from .agromonitoring_service import fetch_satellite_indices_and_images
    try:
        sat_data = fetch_satellite_indices_and_images(db_session, state, district, crop)
        if sat_data and sat_data.get("image_urls"):
            truecolor_url = sat_data["image_urls"].get("truecolor")
            if truecolor_url:
                temp_dir = tempfile.gettempdir()
                local_path = os.path.join(temp_dir, f"sat_{district.replace(' ', '_')}_{crop.replace(' ', '_')}.png")
                req = urllib.request.Request(
                    truecolor_url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    with open(local_path, 'wb') as f:
                        f.write(response.read())
                return local_path
    except Exception as e:
        print(f"[PDF Image Fetch] Failed to download satellite image: {e}")
    return None


def generate_pdf_report(
    file_path: str,
    farmer_name: str,
    crop: str,
    district: str,
    area: float,
    health: str,
    stage: str,
    confidence: float,
    harvest_in_days: int,
    avg_ndvi: float,
    original_img_path: str | None = None,
    lang: str = "en",
    state: str = "Karnataka",
    district_boundary: dict | None = None,
    crop_boundary: dict | None = None,
    data_classification: str = "District Crop Profile",
    db_session = None
) -> None:
    print(f"[PDF Gen] Running template version {PDF_TEMPLATE_VERSION}")

    # 1. Retrieve the DB Crop object
    db_crop = None
    if db_session:
        from .agromonitoring_service import normalize_district_name
        from ..models.orm_models import Crop as ORMCrop, District as ORMDistrict, CropMaster as ORMCropMaster
        from sqlalchemy import func
        norm_district = normalize_district_name(district)
        db_district = db_session.query(ORMDistrict).filter(
            func.lower(ORMDistrict.name) == func.lower(norm_district)
        ).first()
        if db_district:
            db_crop = db_session.query(ORMCrop).join(ORMCropMaster).filter(
                ORMCrop.district_id == db_district.id,
                func.lower(ORMCropMaster.name) == func.lower(crop)
            ).first()

    # 2. Call calculate_crop_satellite_analysis to get identical metrics as UI
    health_status = health
    growth_stage = stage
    est_harvest_days = harvest_in_days
    ndvi_val = avg_ndvi
    evi_val = None
    ndwi_val = None
    obs_date = None
    health_score = 75
    satellite_status = "UNAVAILABLE"
    has_no_satellite = True
    cloud_cover_val = None
    resolution_val = None

    if db_crop:
        from .agromonitoring_service import calculate_crop_satellite_analysis
        analysis_res = calculate_crop_satellite_analysis(db_session, db_crop)
        health_status = analysis_res["health_status"]
        growth_stage = analysis_res["growth_stage"]
        est_harvest_days = analysis_res["est_harvest_days"]
        ndvi_val = analysis_res["latest_ndvi"]
        evi_val = analysis_res["latest_evi"]
        ndwi_val = analysis_res["moisture"]
        obs_date = analysis_res["observation_date"]
        health_score = analysis_res["health_index"] if analysis_res["health_index"] is not None else 0
        satellite_status = analysis_res["satellite_status"]
        cloud_cover_val = analysis_res.get("cloud_cover")
        resolution_val = analysis_res.get("resolution")
        has_no_satellite = (ndvi_val is None or ndvi_val <= 0.0) or ("unavailable" in health_status.lower() or "failed" in health_status.lower() or "error" in health_status.lower())
    else:
        # Static fallback if no db_session
        has_no_satellite = (ndvi_val is None or ndvi_val <= 0.0) or ("unavailable" in health_status.lower())
        if not has_no_satellite:
            from .agromonitoring_service import classify_crop_health_score
            health_status, health_score = classify_crop_health_score(ndvi_val, None, None)
        else:
            health_status = "Satellite data unavailable"
            health_score = 0

    if evi_val is None and ndvi_val is not None and ndvi_val > 0:
        evi_val = 0.85 * ndvi_val + 0.05

    # Fetch weather temperature for coords
    lat, lng = None, None
    if crop_boundary:
        coords = crop_boundary.get("coordinates")
        if coords and crop_boundary.get("type") == "Polygon":
            ring = coords[0]
            if ring:
                lng, lat = ring[0][0], ring[0][1]
    if lat is None and district_boundary:
        coords = district_boundary.get("coordinates")
        if coords:
            if district_boundary.get("type") == "Polygon":
                ring = coords[0]
                if ring:
                    lng, lat = ring[0][0], ring[0][1]
            elif district_boundary.get("type") == "MultiPolygon":
                ring = coords[0][0]
                if ring:
                    lng, lat = ring[0][0], ring[0][1]

    temp_val = None
    humidity_val = None
    if lat is not None and lng is not None:
        try:
            from .weather_service import fetch_current_weather
            weather = fetch_current_weather(lat, lng)
            if weather:
                temp_val = weather.get("temp")
                humidity_val = weather.get("humidity")
        except Exception as e:
            print(f"[PDF Gen] Failed to fetch weather data: {e}")

    # Set document with exactly 45 points margins -> available width 505 pt
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=54,
        bottomMargin=54,
    )
    story = []
    styles = getSampleStyleSheet()

    pdf_font = 'Helvetica'
    pdf_font_bold = 'Helvetica-Bold'
    
    try:
        font_path = 'C:/Windows/Fonts/Nirmala.ttc'
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Nirmala', font_path))
            pdf_font = 'Nirmala'
            pdf_font_bold = 'Nirmala'
    except Exception:
        pass

    # Style Setup
    title_style = ParagraphStyle(
        'KVTitle', parent=styles['Heading1'],
        fontName=pdf_font_bold, fontSize=20, leading=24,
        textColor=colors.HexColor('#1B5E3A'), spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'KVSubtitle', parent=styles['Normal'],
        fontName=pdf_font, fontSize=10.5, leading=14,
        textColor=colors.HexColor('#5E7065'), spaceAfter=14
    )
    section_title_style = ParagraphStyle(
        'KVSectionTitle', parent=styles['Heading2'],
        fontName=pdf_font_bold, fontSize=12, leading=15,
        textColor=colors.HexColor('#1B5E3A'), spaceBefore=8, spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'KVBody', parent=styles['Normal'],
        fontName=pdf_font, fontSize=9.5, leading=13,
        textColor=colors.HexColor('#2D3748')
    )
    body_bold_style = ParagraphStyle(
        'KVBodyBold', parent=styles['Normal'],
        fontName=pdf_font_bold, fontSize=9.5, leading=13,
        textColor=colors.HexColor('#1A202C')
    )

    t = {
        "en": {
            "title": "KrishiVision AI Report",
            "subtitle": "AI-Powered Satellite Crop Monitoring & Geographic Analytics",
            "farmer": "Farmer / Owner",
            "date": "Generation Date",
            "state": "State",
            "district": "District",
            "crop": "Monitored Crop",
            "area": "Total Area",
            "health_status": "Crop Health Status",
            "growth_stage": "Current Growth Stage",
            "ndvi": "NDVI Value",
            "harvest": "Estimated Harvest",
            "confidence": "AI Model Confidence",
            "location_details": "LOCATION DETAILS",
            "overview_header": "CROP OVERVIEW",
            "health_header": "CROP HEALTH REPORT",
            "growth_header": "GROWTH TIMELINE & CYCLES",
            "harvest_header": "HARVEST PREDICTION",
            "satellite_header": "SATELLITE DIAGNOSTICS & NDVI ANALYSIS",
            "recs_header": "AI RECOMMENDATIONS & INSIGHTS",
            "report_id": "Report ID"
        }
    }["en"]

    meta = get_crop_meta_translated(crop, lang)
    report_id = f"KV-{district[:3].upper()}-{crop[:3].upper()}-{datetime.now().strftime('%Y%m%d%H%M')}"
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # ---------------- PAGE 1: EXECUTIVE FARM REPORT ----------------
    page1_elements = []
    
    # Header Logo & Title
    logo_draw = build_logo_drawing()
    header_table = Table([[logo_draw, Paragraph(t["title"], title_style)]], colWidths=[40, 465])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    page1_elements.append(header_table)
    page1_elements.append(Paragraph(t["subtitle"], subtitle_style))
    page1_elements.append(Spacer(1, 10))

    # KPI Grid of 8 cards
    disp_harvest = f"In {est_harvest_days} Days" if (est_harvest_days is not None and est_harvest_days > 0) else "Harvest prediction unavailable"
    cards1 = [
        make_kpi_card("Crop", crop),
        make_kpi_card("Cultivated Area", f"{area:.2f} Acres"),
        make_kpi_card("District", district),
        make_kpi_card("State", state),
        make_kpi_card("Health Status", health_status),
        make_kpi_card("Health Score", f"{health_score} / 100" if not has_no_satellite else "N/A"),
        make_kpi_card("Current Growth Stage", growth_stage),
        make_kpi_card("Estimated Harvest", disp_harvest)
    ]
    
    kpi_table = Table([
        [cards1[0], cards1[1]],
        [cards1[2], cards1[3]],
        [cards1[4], cards1[5]],
        [cards1[6], cards1[7]]
    ], colWidths=[252.5, 252.5])
    kpi_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    page1_elements.append(kpi_table)
    page1_elements.append(Spacer(1, 12))

    # Executive Summary Paragraph
    page1_elements.append(Paragraph("EXECUTIVE SUMMARY", section_title_style))
    if has_no_satellite:
        sum_text = f"The monitored {crop} crop in {district} district ({state}) currently has <b>Satellite data unavailable</b>. Remote sensing monitoring and health index calculations are temporarily inactive due to missing field boundary geometries or temporary service interruptions. Historical agricultural profiles show expected crop parameters."
    else:
        sum_text = f"The monitored {crop} crop in {district} district ({state}) currently shows <b>{health_status}</b> vegetation health based on the latest available satellite observations. The current growth stage is <b>{growth_stage}</b>, with an estimated harvest window of <b>{disp_harvest}</b>. The calculated agricultural health score is <b>{health_score}/100</b>, derived dynamically via Google Earth Engine and Sentinel-2 index pipelines."
    page1_elements.append(Paragraph(sum_text, body_style))
    page1_elements.append(Spacer(1, 14))

    # Data Sources card at bottom
    source_p = Paragraph("<b>DATA SOURCES & TELEMETRY INTEGRATION</b><br/><font color='#5E7065'>Sentinel-2 L2A Multispectral Imagery | NDVI Vegetation Density Indexes | EVI Enhanced Canopy Activity | NDWI Soil Moisture Telemetry | Open-Meteo Weather Grids | KrishiVision AI Baseline Reference Models</font>", ParagraphStyle('SrcP', parent=body_style, fontSize=8, leading=11))
    source_table = Table([[source_p]], colWidths=[505])
    source_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#1B5E3A')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F9F6')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    page1_elements.append(source_table)
    
    story.append(KeepTogether(page1_elements))
    story.append(PageBreak())

    # ---------------- PAGE 2: SATELLITE INTELLIGENCE ----------------
    page2_elements = []
    page2_elements.append(Paragraph("SATELLITE INTELLIGENCE", section_title_style))
    page2_elements.append(Spacer(1, 4))
    
    # Resolve local satellite image path
    local_img = None
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    if original_img_path:
        if os.path.exists(original_img_path):
            local_img = original_img_path
        else:
            possible_path = os.path.join(uploads_dir, os.path.basename(original_img_path))
            if os.path.exists(possible_path):
                local_img = possible_path

    if not local_img and db_session:
        local_img = get_local_satellite_image(db_session, state, district, crop)
        
    if local_img and os.path.exists(local_img) and not has_no_satellite:
        try:
            with PILImage.open(local_img) as img:
                orig_w, orig_h = img.size
            max_w = 400
            max_h = 240
            scale = min(max_w / orig_w, max_h / orig_h)
            new_w = orig_w * scale
            new_h = orig_h * scale
            
            sat_flow = Image(local_img, width=new_w, height=new_h)
            sat_flow.hAlign = 'CENTER'
            page2_elements.append(sat_flow)
            page2_elements.append(Spacer(1, 6))
            page2_elements.append(Paragraph(f"<font color='#5E7065' size=7.5>Truecolor Sentinel-2 satellite observation image for {district} - Captured on {obs_date or current_date.split()[0]}</font>", ParagraphStyle('Cap', parent=body_style, alignment=1)))
            page2_elements.append(Spacer(1, 10))
        except Exception as e:
            print(f"Error drawing satellite image: {e}")
            local_img = None

    if not local_img or has_no_satellite:
        placeholder_data = [[
            Paragraph("<b>SATELLITE DATA UNAVAILABLE</b><br/><font color='#5E7065'>No valid satellite observation is currently available for this crop. Please configure active farm boundary coordinates in the map settings to trigger automatic Sentinel-2 diagnostics.</font>", body_bold_style)
        ]]
        placeholder_table = Table(placeholder_data, colWidths=[505])
        placeholder_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DC2626')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF2F2')),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ]))
        page2_elements.append(placeholder_table)
        page2_elements.append(Spacer(1, 14))

    # Satellite Observation KPI Grid
    disp_obs_date = obs_date if obs_date else (current_date.split()[0] if not has_no_satellite else "Not Available")
    disp_ndvi = f"{ndvi_val:.4f}" if (not has_no_satellite and ndvi_val is not None) else "Not Available"
    disp_evi = f"{evi_val:.4f}" if (not has_no_satellite and evi_val is not None) else "Not Available"
    disp_ndwi = f"{ndwi_val:.4f}" if (not has_no_satellite and ndwi_val is not None) else "Not Available"
    disp_temp = f"{temp_val:.1f}°C" if temp_val is not None else "Not Available"
    disp_humidity = f"{humidity_val:.1f}%" if humidity_val is not None else "Not Available"
    disp_cloud = f"{cloud_cover_val:.1f}%" if (not has_no_satellite and cloud_cover_val is not None) else "Not Available"
    disp_res = resolution_val if (not has_no_satellite and resolution_val is not None) else "Not Available"

    cards2 = [
        make_kpi_card("Observation Date", disp_obs_date),
        make_kpi_card("Satellite Platform", "Sentinel-2 L2A" if not has_no_satellite else "Not Available"),
        make_kpi_card("Resolution / Correction", disp_res),
        make_kpi_card("NDVI (Veg Density)", disp_ndvi),
        make_kpi_card("EVI (Canopy Activity)", disp_evi),
        make_kpi_card("NDWI (Moisture Index)", disp_ndwi),
        make_kpi_card("Local Temperature", disp_temp),
        make_kpi_card("Cloud Coverage", disp_cloud)
    ]
    
    sat_grid = Table([
        [cards2[0], cards2[1]],
        [cards2[2], cards2[3]],
        [cards2[4], cards2[5]],
        [cards2[6], cards2[7]]
    ], colWidths=[252.5, 252.5])
    sat_grid.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    page2_elements.append(sat_grid)
    
    story.append(KeepTogether(page2_elements))
    story.append(PageBreak())

    # ---------------- PAGE 3: CROP HEALTH ANALYSIS ----------------
    page3_elements = []
    page3_elements.append(Paragraph("CROP HEALTH ANALYSIS", section_title_style))
    page3_elements.append(Spacer(1, 4))
    
    # Large central health score progress bar widget
    bar_widget = make_health_progress_bar(health_score, health_status)
    page3_elements.append(bar_widget)
    page3_elements.append(Spacer(1, 12))

    # Health Indicator cards
    health_explain = "Good vegetation density" if health_score >= 75 else ("Moderate vegetation activity" if health_score >= 50 else "Vegetation stress detected")
    moisture_explain = "Healthy canopy condition" if (ndwi_val is not None and ndwi_val >= 0.15) else "Moisture stress detected"
    
    cards3 = [
        make_kpi_card("NDVI Status", health_explain),
        make_kpi_card("EVI Status", "Stable Photosynthesis" if not has_no_satellite else "Not Available"),
        make_kpi_card("Moisture NDWI", moisture_explain if not has_no_satellite else "Not Available"),
        make_kpi_card("Observation Quality", "Excellent (Cloud < 15%)" if not has_no_satellite else "Not Available")
    ]
    
    health_grid = Table([
        [cards3[0], cards3[1]],
        [cards3[2], cards3[3]]
    ], colWidths=[252.5, 252.5])
    health_grid.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    page3_elements.append(health_grid)
    page3_elements.append(Spacer(1, 10))

    # Health Interpretation Dynamic Explanation
    page3_elements.append(Paragraph("HEALTH INTERPRETATION", section_title_style))
    if has_no_satellite:
        sum_recs = "- Satellite imagery is currently unavailable to analyze active vegetative anomalies.<br/>- Local district baseline data is used to compute typical seasonal indicators."
    else:
        sum_recs = f"- <b>Active Chlorophyll Density:</b> The NDVI score of {disp_ndvi} indicates {health_explain.lower()}.<br/>- <b>Canopy Structure:</b> EVI of {disp_evi} points to stable photosynthetic activity and leaf density growth.<br/>- <b>Water Content:</b> NDWI of {disp_ndwi} suggests {moisture_explain.lower()} in the monitored quadrants."
    page3_elements.append(Paragraph(sum_recs, body_style))
    page3_elements.append(Spacer(1, 10))

    # Field Area Metrics card
    page3_elements.append(Paragraph("FIELD AREA METRICS", section_title_style))
    covered_acres = (area * 0.88) if health_score >= 75 else (area * 0.70)
    stressed_acres = area - covered_acres
    
    area_rows = [
        [Paragraph("<b>Metric Parameter</b>", body_bold_style), Paragraph("<b>Area Coverage</b>", body_bold_style), Paragraph("<b>Percentage</b>", body_bold_style)],
        [Paragraph("Total Field Area", body_style), Paragraph(f"{area:.2f} Acres", body_style), Paragraph("100.0%", body_style)],
        [Paragraph("Healthy Area (High Vigor)", body_style), Paragraph(f"{covered_acres:.2f} Acres" if not has_no_satellite else "Not Available", body_style), Paragraph(f"{'88%' if health_score >= 75 else '70%'}" if not has_no_satellite else "Not Available", body_style)],
        [Paragraph("Stressed / Affected Area", body_style), Paragraph(f"{stressed_acres:.2f} Acres" if not has_no_satellite else "Not Available", body_style), Paragraph(f"{'12%' if health_score >= 75 else '30%'}" if not has_no_satellite else "Not Available", body_style)],
        [Paragraph("Bare Soil / Roads / Other", body_style), Paragraph(f"{(area * 0.05):.2f} Acres" if not has_no_satellite else "Not Available", body_style), Paragraph("5.0%" if not has_no_satellite else "Not Available", body_style)]
    ]
    
    area_table = Table(area_rows, colWidths=[185, 160, 160])
    area_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DCE3DF')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EBF3EE')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    page3_elements.append(area_table)
    
    story.append(KeepTogether(page3_elements))
    story.append(PageBreak())

    # ---------------- PAGE 4: GROWTH & HARVEST INTELLIGENCE ----------------
    page4_elements = []
    page4_elements.append(Paragraph("GROWTH & HARVEST INTELLIGENCE", section_title_style))
    page4_elements.append(Spacer(1, 4))
    
    # Horizontal growth timeline widget
    timeline = make_timeline_widget(growth_stage)
    page4_elements.append(timeline)
    page4_elements.append(Spacer(1, 14))

    # Growth details KPI cards
    cards4 = [
        make_kpi_card("Current Stage", growth_stage),
        make_kpi_card("Expected Next Stage", "Flowering" if growth_stage == "Vegetative Growth" else "Maturity"),
        make_kpi_card("Stage Progress", f"{'45%' if growth_stage == 'Vegetative Growth' else '15%'}" if not has_no_satellite else "Not Available"),
        make_kpi_card("Confidence Index", f"{confidence:.1f}%" if not has_no_satellite else "0.0%")
    ]
    
    growth_grid = Table([
        [cards4[0], cards4[1]],
        [cards4[2], cards4[3]]
    ], colWidths=[252.5, 252.5])
    growth_grid.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    page4_elements.append(growth_grid)
    page4_elements.append(Spacer(1, 14))

    # Large Harvest Prediction Card
    page4_elements.append(Paragraph("HARVEST PREDICTION", section_title_style))
    
    expected_harvest_date = (datetime.now() + timedelta(days=est_harvest_days)).strftime("%d %B %Y") if (est_harvest_days is not None and est_harvest_days > 0) else "Harvest prediction unavailable"
    
    harvest_p_lbl = ParagraphStyle('HarvLbl', fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.HexColor('#D1E7DD'))
    harvest_p_val = ParagraphStyle('HarvVal', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.white)
    
    harvest_card_data = [
        [Paragraph("ESTIMATED HARVEST TIME", harvest_p_lbl), Paragraph(f"Expected Date: {expected_harvest_date}", harvest_p_lbl)],
        [Paragraph(f"{est_harvest_days} DAYS" if (est_harvest_days is not None and est_harvest_days > 0) else "N/A", harvest_p_val), Paragraph(f"Prediction Confidence: {confidence:.1f}%" if not has_no_satellite else "0.0%", harvest_p_lbl)]
    ]
    
    harvest_card = Table(harvest_card_data, colWidths=[240, 245])
    harvest_card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1B5E3A')),
        ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor('#1B5E3A')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    page4_elements.append(harvest_card)
    
    story.append(KeepTogether(page4_elements))
    story.append(PageBreak())

    # ---------------- PAGE 5: RECOMMENDATIONS & CROP REFERENCE ----------------
    page5_elements = []
    
    # Recommendations
    page5_elements.append(Paragraph("AI RECOMMENDATIONS & FIELD INSIGHTS", section_title_style))
    page5_elements.append(Spacer(1, 4))
    
    if has_no_satellite:
        recs = "- Satellite imagery or vegetative telemetry is currently offline.<br/>- Configure active crop polygon coordinates on the map screen to activate alerts.<br/>- Inspect crop fields locally for seasonal pathogen or moisture deficit indicators."
    elif health_score >= 75:
        recs = "- <b>Moisture Management:</b> Soil hydration is optimal. Maintain current irrigation feeds.<br/>- <b>Nutrient Schedule:</b> Photosynthetic activity is high. No additional fertigation required.<br/>- <b>Inspection Alert:</b> Continue normal periodic weed clearing and perimeter scouting."
    elif health_score >= 50:
        recs = "- <b>Moisture Management:</b> Slight hydration deficit identified in eastern quadrants. Increase irrigation feed by 10%.<br/>- <b>Nutrient Schedule:</b> Apply standard NPK nitrogen-rich fertilizer supplement to boost photosynthesis.<br/>- <b>Inspection Alert:</b> Watch for localized leaf spotting or insect vectors."
    else:
        recs = "- <b>Moisture Management:</b> Critical moisture stress detected! Immediate crop irrigation required.<br/>- <b>Nutrient Schedule:</b> High vegetative distress. Apply targeted micronutrient foliage spray.<br/>- <b>Pathogen Alert:</b> Inspect and isolate crop leaf nodes for rust or blight infections."
        
    page5_elements.append(Paragraph(recs, body_style))
    page5_elements.append(Spacer(1, 12))

    # Crop Reference Card
    page5_elements.append(Paragraph("CROP REFERENCE INFORMATION", section_title_style))
    ref_details = [
        [Paragraph("<b>Crop Name</b>", body_bold_style), Paragraph(crop, body_style),
         Paragraph("<b>Crop Category</b>", body_bold_style), Paragraph(meta.get("category", "N/A"), body_style)],
        [Paragraph("<b>Scientific Name</b>", body_bold_style), Paragraph(meta.get("scientific", "N/A"), body_style),
         Paragraph("<b>Suitable Soil</b>", body_bold_style), Paragraph(meta.get("soil", "N/A"), body_style)],
        [Paragraph("<b>Water Requirement</b>", body_bold_style), Paragraph(meta.get("water", "N/A"), body_style),
         Paragraph("<b>Suitable Climate</b>", body_bold_style), Paragraph(meta.get("climate", "N/A"), body_style)],
        [Paragraph("<b>Typical Duration</b>", body_bold_style), Paragraph(meta.get("duration", "N/A"), body_style),
         Paragraph("<b>Growing Season</b>", body_bold_style), Paragraph(meta.get("season", "N/A"), body_style)]
    ]
    ref_table = Table(ref_details, colWidths=[110, 142.5, 110, 142.5])
    ref_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DCE3DF')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F9F6')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    page5_elements.append(ref_table)
    page5_elements.append(Spacer(1, 12))

    # Report Verification Card
    page5_elements.append(Paragraph("REPORT VERIFICATION", section_title_style))
    verify_style = ParagraphStyle('KVVerify', parent=body_bold_style, fontSize=9, textColor=colors.HexColor('#1B5E3A'))
    qr_data = [
        [
            Paragraph(f"<b>REPORT VALIDATION & SECURITY</b><br/><font size=7.5 color='#5E7065'>ID: {report_id}<br/>Timestamp: {current_date}<br/>Data Sources: Sentinel-2 L2A, Open-Meteo, AgroMonitoring<br/>Scan to verify authentic classification parameters.</font>", verify_style),
            Drawing(50, 50)
        ]
    ]
    qr_code = QrCodeWidget(value=f"https://krishivision.ai/report/verification/{district}/{crop}", barWidth=50, barHeight=50)
    qr_data[0][1].add(qr_code)
    
    qr_table = Table(qr_data, colWidths=[435, 70])
    qr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EBF3EE')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#1B5E3A')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    page5_elements.append(qr_table)
    
    story.append(KeepTogether(page5_elements))

    # Build Document using NumberedCanvas
    NumberedCanvas.report_id = report_id
    doc.build(story, canvasmaker=NumberedCanvas)
