package org.example.sillylittleguys;

import javafx.application.Application;
import javafx.stage.Stage;
import javafx.scene.Scene;
import javafx.scene.control.Menu;
import javafx.scene.control.MenuBar;
import javafx.scene.control.MenuItem;
import javafx.scene.control.TextArea;
import javafx.scene.layout.BorderPane;
import javafx.stage.FileChooser;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class SillyVisualizer extends Application {

    private TextArea textArea;

    @Override
    public void start(Stage primaryStage) {
        primaryStage.setTitle("Source Code Visualizer");

        textArea = new TextArea();
        textArea.setWrapText(true);

        MenuBar menuBar = new MenuBar();
        Menu fileMenu = new Menu("File");
        MenuItem openItem = new MenuItem("Open");
        openItem.setOnAction(e -> openFile(primaryStage));
        fileMenu.getItems().add(openItem);
        menuBar.getMenus().add(fileMenu);

        BorderPane root = new BorderPane();
        root.setTop(menuBar);
        root.setCenter(textArea);

        Scene scene = new Scene(root, 800, 600);
        primaryStage.setScene(scene);
        primaryStage.show();
    }

    private void openFile(Stage stage) {
        FileChooser fileChooser = new FileChooser();
        fileChooser.getExtensionFilters().addAll(
                new FileChooser.ExtensionFilter("All Coding Files", "*.java", "*.py", "*.c", "*.cpp", "*.js", "*.html", "*.css"),
                new FileChooser.ExtensionFilter("Java Files", "*.java"),
                new FileChooser.ExtensionFilter("Python Files", "*.py"),
                new FileChooser.ExtensionFilter("C Files", "*.c"),
                new FileChooser.ExtensionFilter("C++ Files", "*.cpp"),
                new FileChooser.ExtensionFilter("JavaScript Files", "*.js"),
                new FileChooser.ExtensionFilter("HTML Files", "*.html"),
                new FileChooser.ExtensionFilter("CSS Files", "*.css"),
                new FileChooser.ExtensionFilter("All Files", "*.*")
        );
        File file = fileChooser.showOpenDialog(stage);
        if (file != null) {
            try {
                String content = new String(Files.readAllBytes(Paths.get(file.getAbsolutePath())));
                textArea.setText(content);
            } catch (IOException ex) {
                ex.printStackTrace();
            }
        }
    }

    public static void main(String[] args) {
        launch(args);
    }
}
