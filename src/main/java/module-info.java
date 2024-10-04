module org.example.sillylittleguys {
    requires javafx.controls;
    requires javafx.fxml;
    requires java.desktop;


    opens org.example.sillylittleguys to javafx.fxml;
    exports org.example.sillylittleguys;
}