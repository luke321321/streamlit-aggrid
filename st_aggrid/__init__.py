import os
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import simplejson
import warnings
from dotenv import load_dotenv
import typing

from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode, DataReturnMode, JsCode, walk_gridOptions
from numbers import Number

load_dotenv()

_RELEASE = os.getenv("AGGRID_RELEASE", "true").lower() == "true"

if not _RELEASE:
    _component_func = components.declare_component(
        "agGrid",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend", "build")
    _component_func = components.declare_component("agGrid", path=build_dir)


def AgGrid(
    dataframe: pd.DataFrame,
    gridOptions: typing.Dict = None,
    height: int = 400,
    width=None,
    fit_columns_on_grid_load: bool = False,
    update_mode: GridUpdateMode = "value_changed",
    data_return_mode: DataReturnMode = "as_input",
    allow_unsafe_jscode: bool = False,
    enable_enterprise_modules: bool = False,
    license_key: str = None,
    try_to_convert_back_to_original_types: bool = True,
    conversion_errors: str = "coerce",
    reload_data: bool = False,
    theme: str = "light",
    key: typing.Any = None,
    **default_column_parameters,
) -> typing.Dict:
    """
    Render the Grid Component using the ag-Grid JavaScript library and a dataframe.

    Args:
        dataframe:
            The underlying dataframe to be displayed in the grid.

        gridOption: 
            A dictionary of options for ag-grid. Documentation on http://www.ag-grid.com
            If None default grid options will be created with GridOptionsBuilder.from_dataframe() call.

        height:
            The grid height, by default 400

        width:
            The grid width, by default None
            .. deprecated:: 0.2.0

        fit_columns_on_grid_load:
            Automatically fit columns to the grid width. Defaults to False.

        update_mode: 
            Defines how the grid will send results back to streamlit.
            must be either a string, one or a bitwise combination of:
                + GridUpdateMode.NO_UPDATE
                + GridUpdateMode.MANUAL
                + GridUpdateMode.VALUE_CHANGED
                + GridUpdateMode.SELECTION_CHANGED
                + GridUpdateMode.FILTERING_CHANGED
                + GridUpdateMode.SORTING_CHANGED
                + GridUpdateMode.MODEL_CHANGED

            .. note::
                When using  *GridUpdateMode.MANUAL* a save button will be drawn on top of grid.
                modes can be combined with bitwise OR operator *|* for instance:
                GridUpdateMode = VALUE_CHANGED | SELECTION_CHANGED | FILTERING_CHANGED | SORTING_CHANGED
            
            Defaults to GridUpdateMode.VALUE_CHANGED.

        data_return_mode:
            Defines how the data will be retrieved from components client side. One of:
                + DataReturnMode.AS_INPUT             -> Returns grid data as inputed. Includes cell editions
                + DataReturnMode.FILTERED             -> Returns filtered grid data, maintains input order
                + DataReturnMode.FILTERED_AND_SORTED  -> Returns grid data filtered and sorted
                
            Defaults to DataReturnMode.AS_INPUT.

        allow_unsafe_jscode:
            Allows javascript code to be injected in gridOptions. Defaults to False.

        enable_enterprise_modules:
            Loads Ag-Grid enterprise modules (check licensing). Defaults to False.

        license_key:
            License key for enterprise modules. Defaults to None.

        try_to_convert_back_to_original_types:
            Attempts to convert back to original data types. Defaults to True.

        conversion_errors:
            Behaviour when conversion fails. One of:
                + 'raise'     -> invalid parsing will raise an exception.
                + 'coerce'    -> then invalid parsing will be set as NaT/NaN.
                + 'ignore'    -> invalid parsing will return the input.
           
            Defaults to 'coerce'.

        reload_data:   
            Force AgGrid to reload data using api calls. Should be false on most use cases. Defaults to False.

        theme:
            Theme used by ag-grid. One of:
                + 'streamlit' -> follows default streamlit colors
                + 'light'     -> ag-grid balham-light theme
                + 'dark'      -> ag-grid balham-dark theme
                + 'blue'      -> ag-grid blue theme
                + 'fresh'     -> ag-grid fresh theme
                + 'material'  -> ag-grid material theme
        
            Defaults to 'light'.

        key (typing.Any, optional):
             Streamlit key argument. Check streamlit's documentation. Defaults to None.

        For convenience, additional keyword arguments will be merged to gridOptions defaultColDef.

    Returns:
        dict: 
            A dictionary with members:
            data -> grid's data, including edited values.
            selected -> list of selected rows
                
    """
    if width:
        warnings.warn(
            "DEPRECATION Warning: width parameter is deprecated and will be removed on next version."
        )

    response = {}
    response["data"] = dataframe
    response["selected_rows"] = []

    # basic numpy types of dataframe
    frame_dtypes = dict(zip(dataframe.columns, (t.kind for t in dataframe.dtypes)))

    # if no gridOptions is passed, builds a default one.
    if gridOptions == None:
        gb = GridOptionsBuilder.from_dataframe(dataframe, **default_column_parameters)
        gridOptions = gb.build()

    def cast_to_serializable(value):
        isoformat = getattr(value, "isoformat", None)

        if (isoformat) and callable(isoformat):
            return isoformat()

        elif isinstance(value, Number):
            if np.isnan(value) or np.isinf(value):
                return value.__str__()

            return value
        else:
            return value.__str__()

    json_frame = dataframe.applymap(cast_to_serializable)
    row_data = json_frame.to_dict(orient="records")
    row_data = simplejson.dumps(row_data, ignore_nan=True)

    if allow_unsafe_jscode:
        walk_gridOptions(
            gridOptions, lambda v: v.js_code if isinstance(v, JsCode) else v
        )

    _available_themes = ["streamlit", "light", "dark", "blue", "fresh", "material"]
    if (not isinstance(theme, str)) or (not theme in _available_themes):
        raise ValueError(
            f"{theme} is not valid. Available options: {_available_themes}"
        )

    try:
        if not isinstance(data_return_mode, (str, DataReturnMode)):
            raise ValueError(f"{data_return_mode} is not valid.")

        if isinstance(data_return_mode, str):
            data_return_mode = DataReturnMode[data_return_mode.upper()]
    except:
        raise ValueError(f"{data_return_mode} is not valid.")

    try:
        if not isinstance(update_mode, (str, GridUpdateMode)):
            raise ValueError(f"{update_mode} is not valid.")

        if isinstance(update_mode, str):
            update_mode = GridUpdateMode[update_mode.upper()]
    except:
        raise ValueError(f"{data_return_mode} is not valid.")

    try:
        component_value = _component_func(
            gridOptions=gridOptions,
            row_data=row_data,
            height=height,
            width=width,
            fit_columns_on_grid_load=fit_columns_on_grid_load,
            update_mode=update_mode,
            data_return_mode=data_return_mode,
            frame_dtypes=frame_dtypes,
            allow_unsafe_jscode=allow_unsafe_jscode,
            enable_enterprise_modules=enable_enterprise_modules,
            license_key=license_key,
            default=None,
            reload_data=reload_data,
            theme=theme,
            key=key,
        )

    except components.components.MarshallComponentException as ex:
        # a more complete error message.
        args = list(ex.args)
        args[
            0
        ] += ". If you're using custom JsCode objects on gridOptions, ensure that allow_unsafe_jscode is True."
        ex = components.components.MarshallComponentException(*args)
        raise (ex)

    if component_value:
        if isinstance(component_value, str):
            component_value = simplejson.loads(component_value)
        frame = pd.DataFrame(component_value["rowData"])
        original_types = component_value["originalDtypes"]

        if not frame.empty:
            # maybe this is not the best solution. Should it store original types? What happens when grid pivots?
            if try_to_convert_back_to_original_types:
                numeric_columns = {
                    k: v for k, v in original_types.items() if v in ["i", "u", "f"]
                }
                if numeric_columns:
                    frame.loc[:, numeric_columns] = frame.loc[:, numeric_columns].apply(
                        pd.to_numeric, errors=conversion_errors
                    )

                text_columns = {
                    k: v for k, v in original_types.items() if v in ["O", "S", "U"]
                }
                if text_columns:
                    frame.loc[:, text_columns] = frame.loc[:, text_columns].astype(str)

                date_columns = {k: v for k, v in original_types.items() if v in ["M"]}
                if date_columns:
                    frame.loc[:, date_columns] = frame.loc[:, date_columns].apply(
                        pd.to_datetime, errors=conversion_errors
                    )

                timedelta_columns = {
                    k: v for k, v in original_types.items() if v in ["m"]
                }
                if timedelta_columns:

                    def cast_to_timedelta(s):
                        try:
                            return pd.Timedelta(s)
                        except:
                            return s

                    frame.loc[:, timedelta_columns] = frame.loc[
                        :, timedelta_columns
                    ].apply(cast_to_timedelta)

        response["data"] = frame
        response["selected_rows"] = component_value["selectedRows"]

    return response
