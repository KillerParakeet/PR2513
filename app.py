import streamlit as st
import pandas as pd
import numpy as np

st.title('Displaying Data')

# Display a DataFrame
df = pd.DataFrame(
    np.random.randn(10, 5),
    columns=('col %d' % i for i in range(5)))
st.write(df)

# Display a chart
st.line_chart(df)