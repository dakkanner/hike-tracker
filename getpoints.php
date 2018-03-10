<?php
header('Content-Type: application/json');

$servername = "localhost";
$username = "parado91_hkread";
$password = "FfG3*5ZR3w^96VCh";
$dbname = "parado91_hikes";

// Create connection
$conn = mysqli_connect($servername, $username, $password, $dbname);
// Check connection
if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
}

$query = "SELECT * FROM hikepoints";
$result = mysqli_query($conn, $query);

if (mysqli_num_rows($result) > 0) {
    $rowsOut = array();  //declare an array for saving output to
    // output data of each row
    while($row = mysqli_fetch_assoc($result)) {
        $rowsOut[] = $row;
    }
    echo json_encode($rowsOut);
} else {
    echo "0 results";
}
mysqli_close($conn);
?>