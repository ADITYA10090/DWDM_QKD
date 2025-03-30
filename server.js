const express = require('express');
const path = require('path');
const remote = require('./allocate.js');
const { channel } = require('diagnostics_channel');
const cors = require('cors');
const { exec } = require("child_process");

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.static("../frontend/"));

let channelmetrics;

app.get('/api/createchannel', async (req,res)=>{
    //todo-implement this
    // channelmetrics = remote.allocatechannel();
    // console.log(channelmetrics)
    await exec("python least_candidate_from_csv.py", (error, stdout, stderr) => {
        if (error) {
            return res.status(500).json({ error: error.message });
        }
        if (stderr) {
            return res.status(500).json({ error: stderr });
        }
        res.json({ output: stdout });
    });
    // if(channelmetrics==-1){
    //     res.json({allocated:-1});
    // }else{
    //     res.json(channelmetrics);
    // }
})

app.get('/api/closechannel',(req,res)=>{
    console.log("closed channel");
})

app.listen(3100, ()=>{
    console.log("listening at port 3100")
})