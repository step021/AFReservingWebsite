import { useState, useEffect } from 'react';
import api from '../api';

function Home() {
    // State variables for DataLoss creation
    const [dataLoss, setDataLoss] = useState([]);
    const [clientDataLoss, setClientDataLoss] = useState("");
    const [currQuarterDataLoss, setCurrQuarterDataLoss] = useState("");
    const [currentYearDataLoss, setCurrentYearDataLoss] = useState("");
    const [paidCase, setPaidCase] = useState("");
    const [yearOptionsDataLoss, setYearOptionsDataLoss] = useState([]);
    const [quarterOptionsDataLoss, setQuarterOptionsDataLoss] = useState(["Q2", "Q4"]);

    // State variables for adding historical data
    const [clientAdd, setClientAdd] = useState("");
    const [appendClaimsFile, setAppendClaimsFile] = useState(null);
    const [appendReservesFile, setAppendReservesFile] = useState(null);

    // State variables for updating historical data
    const [clientUpdate, setClientUpdate] = useState("");
    const [replaceClaimsFile, setReplaceClaimsFile] = useState(null);
    const [replaceReservesFile, setReplaceReservesFile] = useState(null);
    const [upperBoundUpdate, setUpperBoundUpdate] = useState("");
    const [lowerBoundUpdate, setLowerBoundUpdate] = useState("");

    const currentDate = new Date();
    const currentYearNum = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth() + 1;

    // Fetch data loss entries on component mount
    useEffect(() => {
        getDataLoss();
    }, []);

    const getDataLoss = () => {
        api
            .get("/api/dataloss/")
            .then((res) => res.data)
            .then((data) => {
                setDataLoss(data);
                console.log(data);
            })
            .catch((err) => alert(err));
    };

    const deleteDataLoss = (id) => {
        api
            .delete(`/api/dataloss/delete/${id}/`)
            .then((res) => {
                if (res.status === 204) alert("File deleted!");
                else alert("Failed to delete file.");
                getDataLoss();
            })
            .catch((error) => alert(error));
    };

    const downloadDataLoss = (id) => {
        api
            .get(`/api/dataloss/download/${id}/`, { responseType: 'blob' })
            .then((res) => {
                if (res.status === 200) {
                    const url = window.URL.createObjectURL(new Blob([res.data]));
                    const link = document.createElement("a");
                    link.href = url;
                    link.setAttribute("download", `data_${id}.xlsx`);
                    document.body.appendChild(link);
                    link.click();
                } else {
                    alert("Failed to download file.");
                }
            })
            .catch((error) => alert(error));
    };

    const createDataLoss = (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append("client", clientDataLoss);
        formData.append("curr_quarter", currQuarterDataLoss);
        formData.append("current_year", currentYearDataLoss);
        formData.append("paid_case", paidCase);

        api
            .post("/api/dataloss/", formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            })
            .then((res) => {
                if (res.status === 201) alert("Data Loss Entry Created!");
                else alert("Failed to create data loss entry.");
                getDataLoss();
            })
            .catch((err) => alert(err));
    };

    const handleFileChange = (e) => {
        if (e.target.name === "append_claims_file") {
            setAppendClaimsFile(e.target.files[0]);
        } else if (e.target.name === "append_reserves_file") {
            setAppendReservesFile(e.target.files[0]);
        } else if (e.target.name === "replace_claims_file") {
            setReplaceClaimsFile(e.target.files[0]);
        } else if (e.target.name === "replace_reserves_file") {
            setReplaceReservesFile(e.target.files[0]);
        }
    };

    const handleClientChangeDataLoss = (e) => {
        const selectedClient = e.target.value;
        setClientDataLoss(selectedClient);

        if (selectedClient === "popular_re") {
            setQuarterOptionsDataLoss(["Q4"]);
            setCurrQuarterDataLoss("Q4");
            updateYearOptionsDataLoss("Q4");
        } else if (selectedClient === "optima") {
            setQuarterOptionsDataLoss(["Q2", "Q4"]);
            setCurrQuarterDataLoss("");
            setCurrentYearDataLoss("");
        }
    };

    const handleClientChangeAdd = (e) => {
        const selectedClient = e.target.value;
        setClientAdd(selectedClient);
    };

    const handleClientChangeUpdate = (e) => {
        const selectedClient = e.target.value;
        setClientUpdate(selectedClient);
    };

    const handleQuarterChangeDataLoss = (e) => {
        const selectedQuarter = e.target.value;
        setCurrQuarterDataLoss(selectedQuarter);
        updateYearOptionsDataLoss(selectedQuarter);
    };

    const updateYearOptionsDataLoss = (selectedQuarter) => {
        let years = [];
        if (selectedQuarter === "Q4") {
            for (let i = 2005; i < currentYearNum; i++) {
                years.push(i.toString());
            }
        } else if (selectedQuarter === "Q2") {
            if (currentMonth > 6) {
                for (let i = 2005; i <= currentYearNum; i++) {
                    years.push(i.toString());
                }
            } else {
                for (let i = 2005; i < currentYearNum; i++) {
                    years.push(i.toString());
                }
            }
        }
        setYearOptionsDataLoss(years);
        setCurrentYearDataLoss("");
    };

    const addHistoricalData = (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append("client", clientAdd);
        formData.append("claims_file", appendClaimsFile);
        formData.append("reserves_file", appendReservesFile);

        console.log([...formData]);  // Log form data before sending

        api
            .post("/api/historical-data/append/", formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            })
            .then((res) => {
                if (res.status === 201) alert("Historical Data Added!");
                else alert("Failed to add historical data.");
                // Reset form fields for adding historical data
                setAppendClaimsFile(null);
                setAppendReservesFile(null);
  
            })
            .catch((err) => alert(err));
    };

    const updateHistoricalData = (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append("client", clientUpdate);
        formData.append("claims_file", replaceClaimsFile);
        formData.append("reserves_file", replaceReservesFile);
        formData.append("upper_bound_update", upperBoundUpdate);
        formData.append("lower_bound_update", lowerBoundUpdate);

        console.log([...formData]);  // Log form data before sending

        api
            .post("/api/historical-data/replace/", formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            })
            .then((res) => {
                if (res.status === 201) alert("Historical Data Updated!");
                else alert("Failed to update historical data.");
                // Reset form fields for updating historical data
                setReplaceClaimsFile(null);
                setReplaceReservesFile(null);
                setUpperBoundUpdate("");
                setLowerBoundUpdate("");
            })
            .catch((err) => alert(err));
    };

    const handleUpperBoundUpdateChange = (e) => {
        const selectedDate = e.target.value;
        if (new Date(selectedDate) >= new Date(lowerBoundUpdate)) {
            setUpperBoundUpdate(selectedDate);
        } else if(lowerBoundUpdate === "") {
            setUpperBoundUpdate(selectedDate);
        } else {
            alert("Upper bound must be greater than or equal to lower bound.");
        }
    };

    const handleLowerBoundUpdateChange = (e) => {
        const selectedDate = e.target.value;
        if (new Date(selectedDate) <= new Date(upperBoundUpdate)) {
            setLowerBoundUpdate(selectedDate);
        } else if(upperBoundUpdate === "") {
            setLowerBoundUpdate(selectedDate);
        }else {
            alert("Lower bound must be less than or equal to upper bound.");
        }
    };

    return (
        <div>
            <div>
                <h2>Home</h2>
                {dataLoss.map((dataLoss) => (
                    <div key={dataLoss.id}>
                        <p>{dataLoss.client} {dataLoss.paid_case} analysis for {dataLoss.curr_quarter} {dataLoss.current_year}</p>
                        <button onClick={() => deleteDataLoss(dataLoss.id)}>Delete</button>
                        <button onClick={() => downloadDataLoss(dataLoss.id)}>Download</button>
                    </div>
                ))}
            </div>

            <h2>Add Historical Data</h2>
            <form onSubmit={addHistoricalData}>
                <label htmlFor="client_add">Client:</label>
                <br />
                <select
                    type="text"
                    id="client_add"
                    name="client_add"
                    required
                    onChange={handleClientChangeAdd}
                    value={clientAdd}
                >
                    <option value="">Select an option</option>
                    <option value="optima">Optima Seguros</option>
                    <option value="popular_re">Popular Re</option>
                    <option value="popular_life">Popular Life</option>
                </select>
                <br />
                <label htmlFor="append_claims_file">Claims File:</label>
                <br />
                <input
                    type="file"
                    id="append_claims_file"
                    name="append_claims_file"
                    accept=".xlsx"
                    required
                    onChange={handleFileChange}
                />
                <br />
                <label htmlFor="append_reserves_file">Reserves File:</label>
                <br />
                <input
                    type="file"
                    id="append_reserves_file"
                    name="append_reserves_file"
                    accept=".xlsx"
                    required
                    onChange={handleFileChange}
                />
                <br />
                <input type="submit" value="Add Historical Data" />
            </form>

            <h2>Update Historical Data</h2>
            <form onSubmit={updateHistoricalData}>
                <label htmlFor="client_update">Client:</label>
                <br />
                <select
                    type="text"
                    id="client_update"
                    name="client_update"
                    required
                    onChange={handleClientChangeUpdate}
                    value={clientUpdate}
                >
                    <option value="">Select an option</option>
                    <option value="optima">Optima Seguros</option>
                    <option value="popular_re">Popular Re</option>
                    <option value="popular_life">Popular Life</option>
                </select>
                <br />
                <label htmlFor="replace_claims_file">Replacement Claims File:</label>
                <br />
                <input
                    type="file"
                    id="replace_claims_file"
                    name="replace_claims_file"
                    accept=".xlsx"
                    required
                    onChange={handleFileChange}
                />
                <br />
                <label htmlFor="replace_reserves_file">Replacement Reserves File:</label>
                <br />
                <input
                    type="file"
                    id="replace_reserves_file"
                    name="replace_reserves_file"
                    accept=".xlsx"
                    required
                    onChange={handleFileChange}
                />
                <br />
                <label htmlFor="upper_bound_update">Upper Bound Update:</label>
                <br />
                <input
                    type="date"
                    id="upper_bound_update"
                    name="upper_bound_update"
                    required
                    onChange={handleUpperBoundUpdateChange}
                    value={upperBoundUpdate}
                />
                <br />
                <label htmlFor="lower_bound_update">Lower Bound Update:</label>
                <br />
                <input
                    type="date"
                    id="lower_bound_update"
                    name="lower_bound_update"
                    required
                    onChange={handleLowerBoundUpdateChange}
                    value={lowerBoundUpdate}
                />
                <br />
                <input type="submit" value="Update Historical Data" />
            </form>

            <h2>Create a Data Loss Entry</h2>
            <form onSubmit={createDataLoss}>
                <label htmlFor="client_dataloss">Client:</label>
                <br />
                <select
                    type="text"
                    id="client_dataloss"
                    name="client_dataloss"
                    required
                    onChange={handleClientChangeDataLoss}
                    value={clientDataLoss}
                >
                    <option value="">Select an option</option>
                    <option value="optima">Optima Seguros</option>
                    <option value="popular_re">Popular Re</option>
                    <option value="popular_life">Popular Life</option>
                </select>
                <br />
                <label htmlFor="curr_quarter">Quarter to be Analyzed:</label>
                <br />
                <select
                    id="curr_quarter"
                    name="curr_quarter"
                    required
                    onChange={handleQuarterChangeDataLoss}
                    value={currQuarterDataLoss}
                >
                    <option value="">Select an option</option>
                    {quarterOptionsDataLoss.map((option) => (
                        <option key={option} value={option}>{option}</option>
                    ))}
                </select>
                <br />
                <label htmlFor="current_year">Year to be Analyzed:</label>
                <br />
                <select
                    id="current_year"
                    name="current_year"
                    required
                    onChange={(e) => setCurrentYearDataLoss(e.target.value)}
                    value={currentYearDataLoss}
                >
                    <option value="">Select an option</option>
                    {yearOptionsDataLoss.map((year) => (
                        <option key={year} value={year}>{year}</option>
                    ))}
                </select>
                <br />
                <label htmlFor="paid_case">Paid/Case:</label>
                <br />
                <select
                    id="paid_case"
                    name="paid_case"
                    required
                    onChange={(e) => setPaidCase(e.target.value)}
                    value={paidCase}
                >
                    <option value="">Select an option</option>
                    <option value="paid">Paid</option>
                    <option value="case">Case</option>
                </select>
                <br />
                <input type="submit" value="Submit" />
            </form>
        </div>
    );
}

export default Home;
