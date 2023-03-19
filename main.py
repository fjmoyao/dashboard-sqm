import streamlit as st
from streamlit import session_state as ss
import numpy as np
import pandas as pd
import plotly.express as px



# --------------------- Funciones -------------------------------------
def proyeccion(valor):
    """
    Genera una proyeccion estimada del crecimiento de SQMaker
    """

    count=1
    valores = [valor]
    v = valor
    np.random.seed(31)
    while count <52:
        if count < 8:
            v = v +  v - v*0.25*np.random.rand(1)[0]
        else:
            v = v + v*0.06*np.random.rand(1)[0] - v*0.08*np.random.rand(1)[0]
        valores.append(np.round(v))
        count+=1
    return valores
# ------------------- Session States ------------------------------------
if "busd" not in ss:
    ss.busd =0
if "busd" not in ss:
    ss.squa =0
if "mostrar" not in ss:
    ss.mostrar =False
# ---------------------Side bar---------------------------------
st.sidebar.title("Proyecciones de rentabilidad")
ss.squa = st.sidebar.number_input("**SQUA disponible**", min_value=0)
ss.busd = st.sidebar.number_input("**Saldo en BUSD**", min_value=0)
st.sidebar.metric(label="**Valor SQMaker**", value="3.5$")

bt= st.sidebar.button("Calcular proyección", type="primary")
# --------------------- Variables estáticas ------------------------------

st.title("**Descargo de responsabilidad**")
st.write("""**¡ATENCION!**

La información presentada NO representa ninguna proyección real y solamente se utiliza con fines especulativos y descriptivos para facilitar el proceso de calculo de ganancias al usuario. Estaremos actualizando en tiempo real el comportamiento del precio del SKER una vez se encuentre disponible.""")
#Valor de SQMaker
sqm= 3.5
if bt:
    #Valores de emision con las distintas opciones disponibles para el usuario
    emision = {
        "4%": np.round(ss.busd*0.5,2),
        "3%": np.round(ss.busd*0.4,2),
        "2%": np.round(ss.busd*0.3,2),
        "1%": np.round(ss.busd*0.2,2),
        "0.5%": np.round(ss.busd*0.1),
        "0.25%": np.round(ss.busd*0.05,2),
        "0.1%": np.round(ss.busd*0.025,2),
        "0.05%": np.round(ss.busd*0.015,2),
        "0.01%": np.round(ss.busd*0.0025,2),
    }
    emision =pd.DataFrame(data= emision,
                        index=[0]).T.reset_index()
    emision.columns =["pct_emision", "Valor SQUA necesario"]
    emision["inv_posible"] = ss.squa/emision["Valor SQUA necesario"] >= 1
    emision["sqm_total"] = np.round(ss.busd/sqm,2)
    emision["sqm_semanal"] = emision["sqm_total"] * emision["pct_emision"].str.strip("%").astype("float64")/100


    #Calcula la proyeccion de inversion maximizando el porcentaje de emision
    optimizar=False
    if ss.busd > ss.squa*2:
        optimizar = True
    inv_op ={
        "Paquete BUSD adquirido":ss.squa*2 ,
        "Porcentaje de emisión":"4%",
        "Valor SQUA necesario":ss.squa,
        "SQMaker total": np.round(ss.squa*2 /sqm,2),
        "SQMaker semanal" : np.round((ss.squa*2 /sqm)*0.04, 2)
    }
    inv_op = pd.DataFrame(inv_op, index=[0])

    st.subheader("Perfiles de inversión comprando el saldo total")
    st.dataframe(emision.rename(columns={"pct_emision":"Porcentaje de emisión",
                                    "sqm_total":"SQMaker total","sqm_semanal":"SQMaker semanal", 
                                    "inv_posible":"¿Es viable?"}))
    if optimizar:
        st.subheader("Perfil de inversión optimizando porcentaje de emisión")
        st.table(inv_op.T)


    sqm_proyeccion = proyeccion(sqm)
    semanas = ["w" + str(x) for x in range(1,53)]

    df = pd.DataFrame()
    df["semanas"] = semanas
    df["SQM value"] = sqm_proyeccion


    for pct, value in zip(emision.loc[emision.inv_posible==True,"pct_emision"].values, emision.loc[emision.inv_posible==True,"sqm_semanal"].values):
        df[pct] = value

    if df.shape[1] > 1:
        for i in range(2, df.shape[1]):
            df.iloc[:,i] *= df.iloc[:,1]
    df["4%_optimo"] = df["SQM value"] * inv_op["SQMaker semanal"].values

    #Valores de ganancia acumulados
    df_acumulado = pd.concat([df.iloc[:,[0,1]], df.iloc[:,2:].cumsum()], axis=1)

    #corta la ganancia acumulada al alcanzar el 100% de rentabilidad
    if df.shape[1] > 10:
        ind = df_acumulado[df_acumulado.loc[:,"semanas"] =="w26"].index[0]
        df_acumulado.loc[ind:,"4%"] = df_acumulado.loc[ind-1,"4%"]

    if df.shape[1] > 9:
        ind = df_acumulado[df_acumulado.loc[:,"semanas"] =="w34"].index[0]
        df_acumulado.loc[ind:,"3%"] = df_acumulado.loc[ind-1,"3%"]
    if df.shape[1] > 8:
        ind = df_acumulado[df_acumulado.loc[:,"semanas"] =="w51"].index[0]
        df_acumulado.loc[ind:,"2%"] = df_acumulado.loc[ind-1,"2%"]

    if optimizar:
        ind = df_acumulado[df_acumulado.loc[:,"semanas"] =="w26"].index[0]
        df_acumulado.loc[ind:,"4%_optimo"] = df_acumulado.loc[ind-1,"4%_optimo"]
    else:
        df_acumulado.drop(columns="4%_optimo", inplace=True)

    #df_acumulado.drop(columns=["0.01%", "0.05%", "0.1%"], inplace=True)

    #Se convierte de wide a long
    df_acumulado = pd.melt(df_acumulado, id_vars=['semanas', 'SQM value'], var_name="pct_emision")

    #---------------------- Gráficos -------------------------------------------------
    fig = px.line(df_acumulado, x="semanas", y="value", color="pct_emision",
                title='Ganancia acumulada',
                labels={
        "semanas":"Semana", "value":"Valor acumulado ($)", "pct_emision":"Porcentaje de emisión"
                })
    st.plotly_chart(fig, use_container_width=False)
    #st.
    fig = px.line(df, x="semanas", y="SQM value", title='Proyeccion valor SQM')
    st.plotly_chart(fig, use_container_width=True)

