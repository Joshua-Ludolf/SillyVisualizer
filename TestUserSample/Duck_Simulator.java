/**
Matthew Trevino
Software Engineering I
A4. Duck
 **/
// Behavior interfaces
interface FlyBehavior {
    void fly();
}

interface QuackBehavior {
    void quack();
}

interface SwimBehavior {
    void swim();
}

// Concrete flying behaviors
class FlyWithWings implements FlyBehavior {
    @Override
    public void fly() {
        System.out.println("I can fly with wings!");
    }
}

class NoFly implements FlyBehavior {
    @Override
    public void fly() {
        System.out.println("I can't fly!");
    }
}

// Concrete quacking behaviors
class NormalQuack implements QuackBehavior {
    @Override
    public void quack() {
        System.out.println("Quack quack!");
    }
}

class QuackToBoat implements QuackBehavior {
    @Override
    public void quack() {
        System.out.println("Quacking to boats: QUACK QUACK!");
    }
}

class Squeak implements QuackBehavior {
    @Override
    public void quack() {
        System.out.println("Squeak squeak!");
    }
}

class MuteQuack implements QuackBehavior {
    @Override
    public void quack() {
        System.out.println("<<Silence>>");
    }
}

// Concrete swimming behaviors
class Swim implements SwimBehavior {
    @Override
    public void swim() {
        System.out.println("I can swim!");
    }
}

class NoSwim implements SwimBehavior {
    @Override
    public void swim() {
        System.out.println("I can't swim!");
    }
}

// Abstract Duck class
abstract class Duck {
    protected FlyBehavior flyBehavior;
    protected QuackBehavior quackBehavior;
    protected SwimBehavior swimBehavior;
    protected String name;

    public Duck(String name) {
        this.name = name;
    }

    public void performFly() {
        System.out.print("I am a " + name + ", ");
        flyBehavior.fly();
    }

    public void performQuack() {
        System.out.print("I am a " + name + ", ");
        quackBehavior.quack();
    }

    public void performSwim() {
        System.out.print("I am a " + name + ", ");
        swimBehavior.swim();
    }

    public abstract void display();
}

// Concrete Duck classes
class MallardDuck extends Duck {
    public MallardDuck() {
        super("Mallard Duck");
        flyBehavior = new FlyWithWings();
        quackBehavior = new NormalQuack();
        swimBehavior = new Swim();
    }

    @Override
    public void display() {
        System.out.println("I'm a real Mallard duck");
    }
}

class SanAntonioDuck extends Duck {
    public SanAntonioDuck() {
        super("San Antonio Duck");
        flyBehavior = new FlyWithWings();
        quackBehavior = new QuackToBoat();
        swimBehavior = new Swim();
    }

    public void walk() {
        System.out.println("I am a San Antonio Duck, walking around!");
    }

    @Override
    public void display() {
        System.out.println("I'm a San Antonio duck");
    }
}

class RubberDuck extends Duck {
    public RubberDuck() {
        super("Rubber Duck");
        flyBehavior = new NoFly();
        quackBehavior = new Squeak();
        swimBehavior = new Swim();
    }

    @Override
    public void display() {
        System.out.println("I'm a rubber duck");
    }
}

class DecoyDuck extends Duck {
    public DecoyDuck() {
        super("Decoy Duck");
        flyBehavior = new NoFly();
        quackBehavior = new MuteQuack();
        swimBehavior = new NoSwim();
    }

    @Override
    public void display() {
        System.out.println("I'm a decoy duck");
    }
}

// Main class to test the implementation
public class Duck_Simulator {
    public static void main(String[] args) {
        Duck mallard = new MallardDuck();
        Duck sanAntonio = new SanAntonioDuck();
        Duck rubber = new RubberDuck();
        Duck decoy = new DecoyDuck();

        System.out.println("=== Mallard Duck ===");
        mallard.display();
        mallard.performFly();
        mallard.performQuack();
        mallard.performSwim();

        System.out.println("\n=== San Antonio Duck ===");
        sanAntonio.display();
        sanAntonio.performFly();
        sanAntonio.performQuack();
        sanAntonio.performSwim();
        ((SanAntonioDuck) sanAntonio).walk();

        System.out.println("\n=== Rubber Duck ===");
        rubber.display();
        rubber.performFly();
        rubber.performQuack();
        rubber.performSwim();

        System.out.println("\n=== Decoy Duck ===");
        decoy.display();
        decoy.performFly();
        decoy.performQuack();
        decoy.performSwim();
    }
}