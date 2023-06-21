import os
import re

import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image
from prophet.serialize import model_from_json

directory_path = os.path.join(os.getcwd(), 'data')
modelos = {}
modelos_em_memoria_sell_out = {}
modelos_em_memoria_sell_in = {}
metricas = {}


def get_arquivos_modelo():
    arquivos_modelo = []
    arquivos_modelo.insert(0, '')
    for file_name in os.listdir(get_absolute_path_modelo_dir()):
        if not (file_name.__contains__('.xlsx') | file_name.__contains__('.png')) :
            arquivos_modelo.append(file_name)
        arquivos_modelo = sorted(arquivos_modelo)
    return arquivos_modelo


def popupate_dicts_modelos_metricas():
    pattern = r'[^a-zA-Z0-9]'

    for root, directories, files in os.walk(get_absolute_path_modelo_dir()):
        # print(files)
        for file in files:

            nome_modelo = re.sub(pattern, '', root.split(get_absolute_path_modelo_dir())[1])

            if nome_modelo not in metricas:
                metricas[nome_modelo] = {}
            if nome_modelo not in modelos:
                modelos[nome_modelo] = {}

            if file.endswith('.xlsx'):
                if file.lower().__contains__('sell out'):
                    metricas[nome_modelo]['sell_out'] = os.path.join(root, file)
                else:
                    metricas[nome_modelo]['sell_in'] = os.path.join(root, file)
            else:
                if file.lower().__contains__('sell out'):
                    modelos[nome_modelo]['sell_out'] = os.path.join(root, file)
                else:
                    modelos[nome_modelo]['sell_in'] = os.path.join(root, file)


def get_path_planilha(arquivo):
    return os.path.join(directory_path, arquivo)


def get_absolute_path_modelo_dir():
    return directory_path


def get_path_modelo(modelo):
    return os.path.join(get_absolute_path_modelo_dir(), modelo)


def get_modelo_previsao(modelo, tipo, semanas):
    frame = None
    if tipo == 'sellin':
        if modelo not in modelos_em_memoria_sell_in:
            load_modelo_sell_in(modelo)
        frame = get_previsao(modelo, semanas, modelos_em_memoria_sell_in)
    else:
        if modelo not in modelos_em_memoria_sell_out:
            load_modelo_sell_out(modelo)
        frame = get_previsao(modelo, semanas, modelos_em_memoria_sell_out)

    frame = frame.loc[:, ['ds', 'trend', 'yhat_lower', 'yhat_upper', 'yhat']]
    frame = frame.rename(columns={'ds': 'Semana', 'yhat': 'Vendas', 'yhat_lower': 'Mínimo', 'yhat_upper': 'Máximo'})
    frame['Semana'] = pd.to_datetime(frame['Semana'].dt.strftime('%d/%m/%Y'))

    return frame


def plot_predictions(frame):
    chart_vendas = alt.Chart(frame, height=500, width=1000).mark_circle(size=40, color='red') \
        .encode(
        x='Semana',
        y='Vendas'
    ).interactive()

    # Create the line chart
    chart_lim_inf = alt.Chart(frame).mark_line(color='green', interpolate="natural", strokeWidth=1).encode(
        x='Semana',
        y='Mínimo'
    ).interactive()

    # Create the line chart
    chart_lim_max = alt.Chart(frame).mark_line(color='black',
                                               interpolate="natural", strokeWidth=1).encode(
        x='Semana',
        y='Máximo'
    ).interactive()

    # Create the line chart
    chart_lim_trend = alt.Chart(frame).mark_line(color='orange',
                                                 interpolate="natural", strokeWidth=1.2, strokeDash=(8, 8)).encode(
        x='Semana',
        y='trend'
    ).interactive()

    chart_combined = alt.layer(chart_vendas, chart_lim_inf, chart_lim_max, chart_lim_trend)
    st.altair_chart(chart_combined, theme=None)


def get_previsao(modelo, semanas, dict_modelo):
    m = dict_modelo[modelo]['modelo']
    future = m.make_future_dataframe(periods=semanas, freq='W')
    forecast = m.predict(future)
    return forecast


def load_modelo_sell_out(selectbox_modelo):
    if selectbox_modelo not in modelos_em_memoria_sell_out:
        with open(modelos[selectbox_modelo]['sell_out'], 'r') as fin:
            m = model_from_json(fin.read())  # Load model
            modelos_em_memoria_sell_out[selectbox_modelo] = {}
            modelos_em_memoria_sell_out[selectbox_modelo]['modelo'] = m
            modelos_em_memoria_sell_out[selectbox_modelo]['plot_padrao'] = {}

            future = m.make_future_dataframe(periods=0, freq='W')
            forecast = m.predict(future)
            fig1 = m.plot(forecast);
            fig2 = m.plot_components(forecast, figsize=[9, 9])

            modelos_em_memoria_sell_out[selectbox_modelo]['plot_padrao']['fig1'] = fig1
            modelos_em_memoria_sell_out[selectbox_modelo]['plot_padrao']['fig2'] = fig2

        return m, fig1, fig2

    return modelos_em_memoria_sell_out[selectbox_modelo]['modelo'], \
           modelos_em_memoria_sell_out[selectbox_modelo]['plot_padrao']['fig1'], \
           modelos_em_memoria_sell_out[selectbox_modelo]['plot_padrao']['fig2']


def load_modelo_sell_in(selectbox_modelo):
    if selectbox_modelo not in modelos_em_memoria_sell_in:
        with open(modelos[selectbox_modelo]['sell_in'], 'r') as fin:
            m = model_from_json(fin.read())  # Load model
            modelos_em_memoria_sell_in[selectbox_modelo] = {}
            modelos_em_memoria_sell_in[selectbox_modelo]['modelo'] = m
            modelos_em_memoria_sell_in[selectbox_modelo]['plot_padrao'] = {}

            future = m.make_future_dataframe(periods=0, freq='W')
            forecast = m.predict(future)
            fig1 = m.plot(forecast)
            fig2 = m.plot_components(forecast, figsize=[9, 9])

            modelos_em_memoria_sell_in[selectbox_modelo]['plot_padrao']['fig1'] = fig1
            modelos_em_memoria_sell_in[selectbox_modelo]['plot_padrao']['fig2'] = fig2

        return m, fig1, fig2

    return modelos_em_memoria_sell_out[selectbox_modelo]['modelo'], \
           modelos_em_memoria_sell_out[selectbox_modelo]['plot_padrao']['fig1'], \
           modelos_em_memoria_sell_out[selectbox_modelo]['plot_padrao']['fig2']


def main():
    arquivos_excel = [""]

    image = Image.open(os.path.join(directory_path, 'img.png'))
    st.sidebar.image(image, width=300)

    # Primeira Parte
    st.sidebar.write('_______________')

    for filename in os.listdir(directory_path):
        if filename.endswith('.xlsx'):
            arquivos_excel.append(filename)

    arquivos_excel = sorted(arquivos_excel)
    selectbox_arquivo = st.sidebar \
        .selectbox("Selecionar Arquivo Consolidado", arquivos_excel, key='selectbox_arquivo_key')

    if selectbox_arquivo:
        metadado = pd.read_excel(get_path_planilha(selectbox_arquivo), sheet_name='Metadados - Sell Out',
                                 engine='openpyxl')
        st.dataframe(metadado, hide_index=True)

    tab1, tab2, tab3 = st.tabs(["Sell Out", "Sell In", "Folhetos"])

    with tab1:
        if selectbox_arquivo:
            df_excel_sell_out = pd.read_excel(get_path_planilha(selectbox_arquivo), sheet_name='Sell Out',
                                              engine='openpyxl')
            df_excel_sell_out_renamed = df_excel_sell_out.rename(columns={'ds': 'Semana', 'y': 'Qnt. Vendas'})
            df_excel_sell_out_renamed['Semana'] = pd.to_datetime(
                df_excel_sell_out_renamed['Semana'].dt.strftime('%d/%m/%Y'))
            st.dataframe(df_excel_sell_out_renamed, height=600, width=500, hide_index=True)

    with tab2:
        if selectbox_arquivo:
            df_excel_sell_in = pd.read_excel(get_path_planilha(selectbox_arquivo), sheet_name='Sell in',
                                             engine='openpyxl')
            df_excel_sell_in_renamed = df_excel_sell_in.rename(columns={'ds': 'Semana', 'y': 'Qnt. Vendas'})
            df_excel_sell_in_renamed['Semana'] = pd.to_datetime(
                df_excel_sell_in_renamed['Semana'].dt.strftime('%d/%m/%Y'))
            st.dataframe(df_excel_sell_in, height=600, width=500, hide_index=True)

    with tab3:
        if selectbox_arquivo:
            try:
                df_excel_folhetos = pd.read_excel(get_path_planilha(selectbox_arquivo), sheet_name='Folhetos',
                                                  engine='openpyxl')
                df_excel_folhetos_renamed = df_excel_folhetos.rename(
                    columns={'holiday': 'Nome Folheto', 'ds': 'Semana', 'upper_window': 'Dur. Sem'})
                df_excel_folhetos_renamed['Semana'] = pd.to_datetime(
                    df_excel_folhetos_renamed['Semana'].dt.strftime('%d/%m/%Y'))
                df_excel_folhetos_renamed = df_excel_folhetos_renamed.drop(columns=['lower_window'])
                st.dataframe(df_excel_folhetos_renamed, height=300, width=500, hide_index=True)
            except ValueError:
                st.write('Sem Folhetos')

    st.sidebar.write('_______________')
    st.write('___________________________________________________________________________')

    selectbox_modelo = st.sidebar.selectbox("Selecione o modelo", get_arquivos_modelo(), key='selectbox_modelo_key')

    tab_sell_out, tab_sell_in = st.tabs(["Sell Out", "Sell In"])

    with tab_sell_out:
        if selectbox_modelo:
            tab_modelo_sell_out, tab_metricas_sell_out = st.tabs(["Modelo - Sell Out", "Métricas - Sell Out"])

            with tab_modelo_sell_out:
                m, fig1, fig2 = load_modelo_sell_out(selectbox_modelo)
                st.pyplot(fig1)
                st.pyplot(fig2)

            with tab_metricas_sell_out:
                metricas_sell_out_frame_cross = pd.read_excel(metricas[selectbox_modelo]['sell_out'],
                                                              sheet_name='Cross Validation', engine='openpyxl')
                metricas_sell_out_frame_metrics = pd.read_excel(metricas[selectbox_modelo]['sell_out'],
                                                                sheet_name='Performance Metrics', engine='openpyxl')

                metricas_sell_out_frame_cross_renamed = metricas_sell_out_frame_cross.rename(
                    columns={'ds': 'Semana', 'y': 'Vendas - Real', 'yhat': 'Vendas - Previsão',
                             'yhat_lower': 'Incerteza - Mín', 'yhat_upper': 'Incerteza - Máx', 'cutoff': 'Corte'})
                metricas_sell_out_frame_cross_renamed['Semana'] = metricas_sell_out_frame_cross_renamed[
                    'Semana'].dt.strftime('%d/%m/%Y')
                metricas_sell_out_frame_cross_renamed['Corte'] = metricas_sell_out_frame_cross_renamed[
                    'Corte'].dt.strftime('%d/%m/%Y')

                chart1 = alt.Chart(metricas_sell_out_frame_cross_renamed, height=500, width=700).mark_circle(size=40,
                                                                                                             color='red') \
                    .encode(
                    x='Semana',
                    y='Vendas - Real'
                ).interactive()

                chart2 = alt.Chart(metricas_sell_out_frame_cross_renamed, height=500, width=700).mark_square(size=40,
                                                                                                             color='blue') \
                    .encode(
                    x='Semana',
                    y='Vendas - Previsão'
                ).interactive()

                # Create the line chart
                chart3 = alt.Chart(metricas_sell_out_frame_cross_renamed).mark_line(color='green',
                                                                                    interpolate="natural").encode(
                    x='Semana',
                    y='Incerteza - Mín'
                ).interactive()

                # Create the line chart
                chart4 = alt.Chart(metricas_sell_out_frame_cross_renamed).mark_line(color='black',
                                                                                    interpolate="natural").encode(
                    x='Semana',
                    y='Incerteza - Máx'
                ).interactive()

                # Create the line chart
                chart4 = alt.Chart(metricas_sell_out_frame_cross_renamed).mark_line(color='black',
                                                                                    interpolate="natural").encode(
                    x='Semana',
                    y='Incerteza - Máx'
                ).interactive()

                chart_combined = alt.layer(chart1, chart2)
                chart_combined = alt.layer(chart_combined, chart3)
                chart_combined = alt.layer(chart_combined, chart4)

                st.altair_chart(chart_combined, theme=None)

                st.dataframe(metricas_sell_out_frame_cross_renamed, height=600, width=700, hide_index=True)
                st.write('___________________________________________________________________________')
                st.dataframe(metricas_sell_out_frame_metrics, height=500, width=500, hide_index=True)

    with tab_sell_in:
        if selectbox_modelo:
            tab_modelo_sell_in, tab_metricas_sell_in = st.tabs(["Modelo - Sell In", "Métricas - Sell In"])

            with tab_modelo_sell_in:
                m, fig1, fig2 = load_modelo_sell_in(selectbox_modelo)
                st.pyplot(fig1)
                st.pyplot(fig2, )

            with tab_metricas_sell_in:
                metricas_sell_in_frame_cross = pd.read_excel(metricas[selectbox_modelo]['sell_in'],
                                                             sheet_name='Cross Validation', engine='openpyxl')
                metricas_sell_in_frame_metrics = pd.read_excel(metricas[selectbox_modelo]['sell_in'],
                                                               sheet_name='Performance Metrics', engine='openpyxl')

                metricas_sell_in_frame_cross_renamed = metricas_sell_in_frame_cross.rename(
                    columns={'ds': 'Semana', 'y': 'Vendas - Real', 'yhat': 'Vendas - Previsão',
                             'yhat_lower': 'Incerteza - Mín', 'yhat_upper': 'Incerteza - Máx', 'cutoff': 'Corte'})
                metricas_sell_in_frame_cross_renamed['Semana'] = pd.to_datetime(metricas_sell_in_frame_cross_renamed[
                                                                                    'Semana'].dt.strftime('%d/%m/%Y'))
                metricas_sell_in_frame_cross_renamed['Corte'] = pd.to_datetime(metricas_sell_in_frame_cross_renamed[
                                                                                   'Corte'].dt.strftime('%d/%m/%Y'))

                chart1 = alt.Chart(metricas_sell_in_frame_cross_renamed, height=500, width=700).mark_circle(size=40,
                                                                                                            color='red') \
                    .encode(
                    x='Semana',
                    y='Vendas - Real'
                ).interactive()

                chart2 = alt.Chart(metricas_sell_in_frame_cross_renamed, height=500, width=700).mark_square(size=40,
                                                                                                            color='blue') \
                    .encode(
                    x='Semana',
                    y='Vendas - Previsão'
                ).interactive()

                # Create the line chart
                chart3 = alt.Chart(metricas_sell_in_frame_cross_renamed).mark_line(color='green',
                                                                                   interpolate="natural").encode(
                    x='Semana',
                    y='Incerteza - Mín'
                ).interactive()

                # Create the line chart
                chart4 = alt.Chart(metricas_sell_in_frame_cross_renamed).mark_line(color='black',
                                                                                   interpolate="natural").encode(
                    x='Semana',
                    y='Incerteza - Máx'
                ).interactive()

                # Create the line chart
                chart4 = alt.Chart(metricas_sell_in_frame_cross_renamed).mark_line(color='black',
                                                                                   interpolate="natural").encode(
                    x='Semana',
                    y='Incerteza - Máx'
                ).interactive()

                # Create the line chart
                chart5 = alt.Chart(metricas_sell_in_frame_cross_renamed).mark_line(color='black',
                                                                                   interpolate="natural",
                                                                                   strokeDash=[10, 10]).encode(
                    x='Corte'

                ).interactive()

                chart_combined = alt.layer(chart1, chart2)
                chart_combined = alt.layer(chart_combined, chart3)
                chart_combined = alt.layer(chart_combined, chart4)
                # chart_combined = alt.layer(chart_combined, chart5)

                st.altair_chart(chart_combined, theme=None)

                st.dataframe(metricas_sell_in_frame_cross_renamed, height=600, width=700, hide_index=True)
                st.write('___________________________________________________________________________')
                st.dataframe(metricas_sell_in_frame_metrics, height=500, width=500, hide_index=True)

    st.sidebar.write('_______________')
    st.write('___________________________________________________________________________')
    #
    # selectbox_modelo_previsao = st.sidebar.selectbox("Selecione o modelo para previsões", arquivos_modelo,
    #                                                  key='selectbox_modelo_previsao_key')
    #
    # radio_modelo_previsao = st.sidebar.radio("Selecione Semanas", [12, 18, 24, 32], key="previsao")
    #
    # tab_sell_out_prev, tab_sell_in_prev = st.tabs(["Sell Out", "Sell In"])
    #
    # with tab_sell_out_prev:
    #     if selectbox_modelo_previsao:
    #         if radio_modelo_previsao == 12:
    #             frame = get_modelo_previsao(selectbox_modelo_previsao, 'sellout', 12)
    #             plot_predictions(frame)
    #             st.dataframe(frame, height=600, width=700, hide_index=True)
    #         elif radio_modelo_previsao == 18:
    #             frame = get_modelo_previsao(selectbox_modelo_previsao, 'sellout', 18)
    #             plot_predictions(frame)
    #             st.dataframe(frame, height=600, width=700, hide_index=True)
    #         elif radio_modelo_previsao == 24:
    #             frame = get_modelo_previsao(selectbox_modelo_previsao, 'sellout', 24)
    #             plot_predictions(frame)
    #             st.dataframe(frame, height=600, width=700, hide_index=True)
    #         elif radio_modelo_previsao == 32:
    #             frame = get_modelo_previsao(selectbox_modelo_previsao, 'sellout', 32)
    #             plot_predictions(frame)
    #             st.dataframe(frame, height=600, width=700, hide_index=True)
    #
    # with tab_sell_in_prev:
    #     if selectbox_modelo_previsao:
    #         if radio_modelo_previsao == 12:
    #             frame = get_modelo_previsao(selectbox_modelo_previsao, 'sellin', 12)
    #             plot_predictions(frame)
    #             st.dataframe(frame, height=600, width=700, hide_index=True)
    #         elif radio_modelo_previsao == 18:
    #             frame = get_modelo_previsao(selectbox_modelo_previsao, 'sellin', 18)
    #             plot_predictions(frame)
    #             st.dataframe(frame, height=600, width=700, hide_index=True)
    #         elif radio_modelo_previsao == 24:
    #             frame = get_modelo_previsao(selectbox_modelo_previsao, 'sellin', 24)
    #             plot_predictions(frame)
    #             st.dataframe(frame, height=600, width=700, hide_index=True)
    #         elif radio_modelo_previsao == 32:
    #             frame = get_modelo_previsao(selectbox_modelo_previsao, 'sellin', 32)
    #             plot_predictions(frame)
    #             st.dataframe(frame, height=600, width=700, hide_index=True)


if __name__ == "__main__":
    popupate_dicts_modelos_metricas()
    main()
