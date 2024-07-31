import React from 'react';
import { useNavigate } from 'react-router-dom';
import "../styles/OpeningScreen.css";

function OpeningScreen() {
    const navigate = useNavigate();

    const handleRegister = () => {
        navigate('/register');
    };

    const handleLogin = () => {
        navigate('/login');
    };

    return (
        <div className='opening-container'>
            <h1 className='opening-title'>Welcome to the Reserving Automation Site!</h1>
            <button  className= 'opening-button' onClick={handleRegister}>Register</button>
            <button className= 'opening-button' onClick={handleLogin}>Login</button>
        </div>
    );
}

export default OpeningScreen;